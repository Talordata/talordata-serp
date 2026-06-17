from __future__ import annotations

import base64
import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.serp_action_registry import SerpAction
from utils.serp_action_registry import get_action
from utils.serp_client import DEFAULT_SERP_ENDPOINT
from utils.serp_client import SerpApiError
from utils.serp_client import SerpClient
from utils.serp_normalizer import normalize_image_results
from utils.serp_normalizer import normalize_raw_payload
from utils.serp_normalizer import normalize_web_results


GOOGLE_UULE_ENGINES = {
    "google",
    "google_ai_mode",
    "google_images",
    "google_jobs",
    "google_local",
    "google_shopping",
    "google_videos",
    "google_web",
}
UULE_LENGTH_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def parse_bool(value: Any, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    return bool(value)


def mask_api_key(api_key: str) -> str:
    api_key = str(api_key or "").strip()
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


def parse_params_json(value: Any) -> dict[str, Any]:
    raw = str(value or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("params_json is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("params_json must be a JSON object")
    return parsed


def parse_optional_params_json(value: Any) -> dict[str, Any]:
    try:
        return parse_params_json(value)
    except ValueError:
        return {}


def encode_uule_location(location: str) -> str:
    normalized = str(location or "").strip()
    if not normalized:
        return ""
    length = min(len(normalized), len(UULE_LENGTH_ALPHABET) - 1)
    encoded = base64.urlsafe_b64encode(normalized.encode("utf-8")).decode("ascii").rstrip("=")
    return f"w+CAIQICI{UULE_LENGTH_ALPHABET[length]}{encoded}"


def add_google_uule_from_location(action: SerpAction, params: dict[str, Any]) -> None:
    if action.engine not in GOOGLE_UULE_ENGINES:
        return
    if params.get("uule") not in (None, ""):
        return
    location = str(params.get("location") or "").strip()
    if location:
        params["uule"] = encode_uule_location(location)


def build_action_params(action: SerpAction, tool_parameters: dict[str, Any]) -> dict[str, Any]:
    query = str(tool_parameters.get(action.query_field) or "").strip()
    if not query:
        raise ValueError(f"{action.query_field} is required")

    params: dict[str, Any] = {"engine": action.engine, action.query_field: query}
    for key, value in tool_parameters.items():
        if key in {"engine", "params_json", action.query_field} or value in (None, ""):
            continue
        if key == "no_cache" or isinstance(value, bool):
            params[key] = parse_bool(value)
        else:
            params[key] = value

    extra = parse_optional_params_json(tool_parameters.get("params_json"))
    extra.pop("engine", None)
    params.update({key: value for key, value in extra.items() if value not in (None, "")})
    add_google_uule_from_location(action, params)
    params["engine"] = action.engine
    return params


def normalize_action_payload(action: SerpAction, query: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action.result_type == "image":
        return normalize_image_results(query, action.engine, payload)
    if action.result_type == "web":
        return normalize_web_results(query, action.engine, payload)
    return normalize_raw_payload(query, action.engine, payload)


def invoke_action(
    tool: Tool,
    action: SerpAction,
    tool_parameters: dict[str, Any],
) -> Generator[ToolInvokeMessage, None, None]:
    credentials = tool.runtime.credentials
    api_key = str(credentials.get("serp_api_key") or "").strip()
    endpoint = DEFAULT_SERP_ENDPOINT
    params = build_action_params(action, tool_parameters)
    try:
        payload = SerpClient(api_key=api_key, endpoint=endpoint).request(params)
    except SerpApiError as exc:
        raise SerpApiError(
            exc.status_code,
            f"{exc} (endpoint={endpoint}, key={mask_api_key(api_key)})",
            exc.payload,
        ) from exc

    normalized = normalize_action_payload(action, str(params.get(action.query_field, "")), payload)
    yield tool.create_json_message(normalized)


def make_tool_class(tool_name: str) -> type[Tool]:
    action = get_action(tool_name)

    class GeneratedSerpActionTool(Tool):
        def _invoke(
            self,
            tool_parameters: dict[str, Any],
        ) -> Generator[ToolInvokeMessage, None, None]:
            yield from invoke_action(self, action, tool_parameters)

    GeneratedSerpActionTool.__name__ = "".join(part.title() for part in tool_name.split("_")) + "Tool"
    return GeneratedSerpActionTool
