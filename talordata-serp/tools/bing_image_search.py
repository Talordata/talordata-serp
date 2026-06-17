from __future__ import annotations

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.serp_client import DEFAULT_SERP_ENDPOINT
from utils.serp_client import SerpApiError
from utils.serp_client import SerpClient
from utils.serp_normalizer import normalize_image_results


SUPPORTED_FILTERS = (
    "adlt",
    "imagesize",
    "color2",
    "photo",
    "aspect",
    "face",
    "binglicense",
    "bingage",
)


def mask_api_key(api_key: str) -> str:
    api_key = str(api_key or "").strip()
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


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


def build_bing_image_params(tool_parameters: dict[str, Any]) -> dict[str, Any]:
    query = str(tool_parameters.get("q") or "").strip()
    if not query:
        raise ValueError("q is required")

    params: dict[str, Any] = {
        "engine": "bing_images",
        "q": query,
        "cc": tool_parameters.get("cc") or "us",
        "setlang": tool_parameters.get("setlang") or "en",
        "mkt": tool_parameters.get("mkt") or "en-us",
        "count": int(tool_parameters.get("count") or 10),
        "first": int(tool_parameters.get("first") or 1),
        "no_cache": parse_bool(tool_parameters.get("no_cache")),
    }

    for key in SUPPORTED_FILTERS:
        value = tool_parameters.get(key)
        if value not in (None, ""):
            params[key] = value

    return params


class BingImageSearchTool(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
        ) -> Generator[ToolInvokeMessage, None, None]:
        credentials = self.runtime.credentials
        api_key = str(credentials.get("serp_api_key") or "").strip()
        endpoint = DEFAULT_SERP_ENDPOINT
        params = build_bing_image_params(tool_parameters)
        try:
            payload = SerpClient(api_key=api_key, endpoint=endpoint).request(params)
        except SerpApiError as exc:
            raise SerpApiError(
                exc.status_code,
                f"{exc} (endpoint={endpoint}, key={mask_api_key(api_key)})",
                exc.payload,
            ) from exc
        normalized = normalize_image_results(params["q"], params["engine"], payload)
        yield self.create_json_message(normalized)
