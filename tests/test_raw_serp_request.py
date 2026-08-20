import pytest
from dify_plugin import Tool

from tools.raw_serp_request import RawSerpRequestTool
from tools.raw_serp_request import build_raw_serp_params


def test_raw_serp_request_implements_current_dify_tool_contract():
    assert RawSerpRequestTool._invoke.__code__.co_argcount == Tool._invoke.__code__.co_argcount


def test_build_raw_serp_params_merges_json_params():
    params = build_raw_serp_params(
        {
            "engine": "google",
            "q": "coffee",
            "params_json": '{"gl":"us","hl":"en","num":5}',
        }
    )

    assert params == {
        "engine": "google",
        "q": "coffee",
        "gl": "us",
        "hl": "en",
        "num": 5,
    }


def test_build_raw_serp_params_rejects_missing_engine():
    with pytest.raises(ValueError, match="engine is required"):
        build_raw_serp_params({"q": "coffee"})


def test_build_raw_serp_params_rejects_non_object_json():
    with pytest.raises(ValueError, match="params_json must be a JSON object"):
        build_raw_serp_params({"engine": "google", "q": "coffee", "params_json": "[1,2]"})


def test_build_raw_serp_params_rejects_invalid_json():
    with pytest.raises(ValueError, match="params_json is invalid JSON"):
        build_raw_serp_params({"engine": "google", "q": "coffee", "params_json": "{"})
