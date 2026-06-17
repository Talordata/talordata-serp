def test_provider_module_imports():
    import provider.talordata_serp as talordata_serp

    assert talordata_serp.TalordataSerpProvider.__name__ == "TalordataSerpProvider"


def test_provider_rejects_empty_serp_api_key():
    import pytest
    from dify_plugin.errors.tool import ToolProviderCredentialValidationError

    from provider.talordata_serp import TalordataSerpProvider

    with pytest.raises(ToolProviderCredentialValidationError, match="SERP API key is required"):
        TalordataSerpProvider()._validate_credentials({"serp_api_key": " "})


def test_provider_accepts_credentials_without_upstream_request(monkeypatch):
    from provider.talordata_serp import TalordataSerpProvider

    def fail_on_http_request(*args, **kwargs):
        raise AssertionError("credential validation must not call the SERP upstream")

    monkeypatch.setattr("urllib.request.urlopen", fail_on_http_request)

    TalordataSerpProvider()._validate_credentials({"serp_api_key": "abc123"})


def test_provider_credentials_do_not_expose_serp_endpoint():
    from pathlib import Path

    import yaml

    config = yaml.safe_load(Path("provider/talordata_serp.yaml").read_text(encoding="utf-8"))

    assert list(config["credentials_for_provider"]) == ["serp_api_key"]


def test_provider_ignores_legacy_serp_endpoint_without_upstream_request(monkeypatch):
    from provider.talordata_serp import TalordataSerpProvider

    def fail_on_http_request(*args, **kwargs):
        raise AssertionError("credential validation must not call the SERP upstream")

    monkeypatch.setattr("urllib.request.urlopen", fail_on_http_request)

    TalordataSerpProvider()._validate_credentials(
        {
            "serp_api_key": "prod_key",
            "serp_endpoint": "serpapi.talordata.net/legacy-test-endpoint",
        }
    )


def test_provider_configuration_loads_with_dify_sdk():
    from pathlib import Path

    import yaml
    from dify_plugin.entities.tool import ToolProviderConfiguration

    config = yaml.safe_load(Path("provider/talordata_serp.yaml").read_text(encoding="utf-8"))

    ToolProviderConfiguration(**config)


def test_plugin_entrypoint_imports_with_current_dify_sdk():
    import main

    assert main.plugin is not None


def test_manifest_versions_match():
    from pathlib import Path

    import yaml

    manifest = yaml.safe_load(Path("manifest.yaml").read_text(encoding="utf-8"))

    assert manifest["version"] == manifest["meta"]["version"]
