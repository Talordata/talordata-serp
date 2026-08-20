from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.serp_client import SerpClient


def build_raw_serp_params(tool_parameters: dict[str, Any]) -> dict[str, Any]:
    engine = str(tool_parameters.get("engine") or "").strip()
    if not engine:
        raise ValueError("engine is required")

    params: dict[str, Any] = {"engine": engine}
    query = str(tool_parameters.get("q") or "").strip()
    if query:
        params["q"] = query

    extra_raw = str(tool_parameters.get("params_json") or "").strip()
    if extra_raw:
        try:
            extra = json.loads(extra_raw)
        except json.JSONDecodeError as exc:
            raise ValueError("params_json is invalid JSON") from exc
        if not isinstance(extra, dict):
            raise ValueError("params_json must be a JSON object")
        params.update(extra)

    params["engine"] = engine
    if query:
        params["q"] = query
    return params


class RawSerpRequestTool(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        credentials = self.runtime.credentials
        api_key = str(credentials.get("serp_api_key") or "").strip()
        params = build_raw_serp_params(tool_parameters)
        payload = SerpClient(api_key=api_key).request(params)
        yield self.create_json_message(
            {
                "engine": params["engine"],
                "query": params.get("q", ""),
                "raw": payload,
            }
        )
