from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from utils.constants import DEFAULT_SERP_ENDPOINT


class SerpApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SerpClient:
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_SERP_ENDPOINT,
        timeout: int = 60,
        urlopen: Callable | None = None,
    ):
        api_key = (api_key or "").strip()
        endpoint = (endpoint or DEFAULT_SERP_ENDPOINT).strip()
        if not api_key:
            raise ValueError("SERP API key is required")
        if not endpoint:
            raise ValueError("SERP endpoint is required")

        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self._urlopen = urlopen or globals()["urlopen"]

    def request(self, params: dict[str, Any]) -> dict[str, Any]:
        cleaned = self._clean_params(params)
        request = Request(
            self.endpoint,
            data=urlencode(cleaned).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Origin": "dify",
                "User-Agent": "Talordata-Dify-Plugin/0.1.7",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with self._urlopen(request, timeout=self.timeout) as response:
                status_code = response.status
                response_text = response.read().decode("utf-8")
        except HTTPError as exc:
            response_text = exc.read().decode("utf-8") if exc.fp else str(exc.reason)
            payload = self._parse_response_text(exc.code, response_text)
            message = self._error_message(payload, response_text or str(exc.reason))
            raise SerpApiError(exc.code, message, payload) from exc
        except URLError as exc:
            raise SerpApiError(0, f"SERP API request failed: {exc.reason}") from exc

        payload = self._parse_response_text(status_code, response_text)
        if status_code < 200 or status_code >= 300:
            message = self._error_message(payload, response_text)
            raise SerpApiError(status_code, message, payload)
        if not isinstance(payload, dict):
            raise SerpApiError(status_code, "SERP API returned a non-object JSON response", payload)
        business_error = self._business_error_code(payload)
        if business_error is not None:
            raise SerpApiError(business_error, self._error_message(payload, response_text), payload)
        return payload

    @staticmethod
    def _clean_params(params: dict[str, Any]) -> dict[str, str]:
        params = dict(params or {})
        params.setdefault("json", 2)
        params.setdefault("isjson", 1)
        cleaned: dict[str, str] = {}
        for key, value in (params or {}).items():
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                cleaned[key] = "true" if value else "false"
            else:
                cleaned[key] = str(value)
        return cleaned

    @staticmethod
    def _parse_response_text(status_code: int, text: str) -> Any:
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            preview = SerpClient._response_preview(text)
            message = "SERP API returned invalid JSON"
            if preview:
                message = f"{message}: {preview}"
            raise SerpApiError(status_code, message, text) from exc

    @staticmethod
    def _error_message(payload: Any, fallback: str) -> str:
        if isinstance(payload, dict):
            for key in ("message", "error", "msg", "data"):
                value = payload.get(key)
                if value:
                    return str(value)
        return fallback or "SERP API request failed"

    @staticmethod
    def _business_error_code(payload: dict[str, Any]) -> int | None:
        code = payload.get("code")
        if code in (None, "", 0, "0", 200, "200"):
            return None
        try:
            return int(code)
        except (TypeError, ValueError):
            return 500

    @staticmethod
    def _response_preview(text: str, max_length: int = 300) -> str:
        return " ".join(str(text or "").split())[:max_length]
