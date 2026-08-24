import pytest
import yaml
from dify_plugin import Tool

from tools.bing_image_search import BingImageSearchTool
from tools.bing_image_search import build_bing_image_params


def test_bing_image_search_implements_current_dify_tool_contract():
    assert BingImageSearchTool._invoke.__code__.co_argcount == Tool._invoke.__code__.co_argcount


def test_bing_image_search_query_is_visible_in_workflow_form():
    with open("tools/bing_image_search.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    query_param = next(param for param in config["parameters"] if param["name"] == "q")

    assert query_param["form"] == "form"


def test_build_bing_image_params_maps_defaults():
    params = build_bing_image_params({"q": "coffee"})

    assert params == {
        "engine": "bing_images",
        "q": "coffee",
        "cc": "us",
        "setlang": "en",
        "mkt": "en-us",
        "count": 10,
        "first": 1,
    }


def test_build_bing_image_params_does_not_send_no_cache():
    params = build_bing_image_params({"q": "coffee", "no_cache": True})

    assert "no_cache" not in params


def test_build_bing_image_params_keeps_supported_filters():
    params = build_bing_image_params(
        {
            "q": "coffee",
            "cc": "gb",
            "setlang": "en",
            "mkt": "en-gb",
            "count": 5,
            "first": 11,
            "adlt": "strict",
            "imagesize": "+filterui:imagesize-large",
            "color2": "+filterui:color2-color",
            "photo": "+filterui:photo-photo",
            "aspect": "+filterui:aspect-wide",
            "face": "+filterui:face-face",
            "binglicense": "+filterui:license-L1",
            "bingage": "lt10080",
        }
    )

    assert params["engine"] == "bing_images"
    assert params["q"] == "coffee"
    assert params["count"] == 5
    assert params["first"] == 11
    assert params["adlt"] == "strict"
    assert params["imagesize"] == "+filterui:imagesize-large"


def test_build_bing_image_params_rejects_empty_query():
    with pytest.raises(ValueError, match="q is required"):
        build_bing_image_params({"q": " "})


def test_bing_image_search_uses_production_endpoint_and_ignores_legacy_credential(monkeypatch):
    calls = []

    class FakeRuntime:
        credentials = {
            "serp_api_key": "prod_key",
            "serp_endpoint": "https://devserp.seboll.com/serp/v1/request",
        }

    class FakeSerpClient:
        def __init__(self, api_key, endpoint):
            calls.append(("init", api_key, endpoint))

        def request(self, params):
            calls.append(("request", params))
            return {"images_results": []}

    monkeypatch.setattr("tools.bing_image_search.SerpClient", FakeSerpClient)

    tool = object.__new__(BingImageSearchTool)
    tool.runtime = FakeRuntime()
    monkeypatch.setattr(tool, "create_json_message", lambda payload: payload)

    list(tool._invoke({"q": "pizza"}))

    assert calls[0] == ("init", "prod_key", "https://serpapi.talordata.net/serp/v1/request")


def test_bing_image_search_wraps_serp_errors_with_masked_key(monkeypatch):
    from utils.serp_client import SerpApiError

    class FakeRuntime:
        credentials = {
            "serp_api_key": "a84cde3f505841c8768ebc53267bd74a",
            "serp_endpoint": "https://serpapi.talordata.net/serp/v1/request",
        }

    class FakeSerpClient:
        def __init__(self, api_key, endpoint):
            pass

        def request(self, params):
            raise SerpApiError(401, "API key authentication failed：error-6")

    monkeypatch.setattr("tools.bing_image_search.SerpClient", FakeSerpClient)

    tool = object.__new__(BingImageSearchTool)
    tool.runtime = FakeRuntime()

    with pytest.raises(SerpApiError, match="a84c\\.\\.\\.d74a"):
        list(tool._invoke({"q": "pizza"}))
