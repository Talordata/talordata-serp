from __future__ import annotations

from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class TalordataSerpProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_key = str(credentials.get("serp_api_key") or "").strip()
        if not api_key:
            raise ToolProviderCredentialValidationError("SERP API key is required")
