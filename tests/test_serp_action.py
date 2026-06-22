import pytest

from tools.serp_action import build_action_params
from tools.serp_action import normalize_action_payload
from tools.serp_action import parse_params_json
from utils.serp_action_registry import SerpAction


def test_build_action_params_sets_engine_and_query_field():
    action = SerpAction(
        tool_name="yandex_search",
        engine="yandex",
        label="Yandex Search",
        query_field="text",
        result_type="web",
        source="tools/yandex_search.py",
    )

    params = build_action_params(
        action,
        {
            "text": "coffee",
            "lang": "en",
            "no_cache": "False",
            "params_json": '{"p":2,"engine":"google"}',
        },
    )

    assert params == {
        "engine": "yandex",
        "text": "coffee",
        "lang": "en",
        "no_cache": False,
        "p": 2,
    }


def test_build_action_params_ignores_stale_params_json_for_generated_actions():
    action = SerpAction(
        tool_name="google_search",
        engine="google",
        label="Google Search",
        query_field="q",
        result_type="web",
        source="tools/google_search.py",
    )

    params = build_action_params(
        action,
        {
            "q": "江苏",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "params_json": "{{#sys.query#}}",
        },
    )

    assert params == {
        "engine": "google",
        "q": "江苏",
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
    }


def test_build_action_params_derives_uule_from_google_location_when_blank():
    action = SerpAction(
        tool_name="google_search",
        engine="google",
        label="Google Search",
        query_field="q",
        result_type="web",
        source="tools/google_search.py",
    )

    params = build_action_params(
        action,
        {
            "q": "coffee",
            "location": "United States",
            "uule": "",
        },
    )

    assert params["location"] == "United States"
    assert params["uule"] == "w+CAIQICINVW5pdGVkIFN0YXRlcw"


def test_build_action_params_rejects_missing_required_query_field():
    action = SerpAction(
        tool_name="google_scholar_author_search",
        engine="google_scholar_author",
        label="Google Scholar Author Search",
        query_field="author_id",
        result_type="raw",
        source="tools/google_scholar_author_search.py",
    )

    with pytest.raises(ValueError, match="author_id is required"):
        build_action_params(action, {"author_id": " "})


def test_parse_params_json_rejects_non_object_json():
    with pytest.raises(ValueError, match="params_json must be a JSON object"):
        parse_params_json("[1,2]")


def test_normalize_action_payload_uses_result_type():
    image_action = SerpAction(
        tool_name="google_image_search",
        engine="google_images",
        label="Google Image Search",
        query_field="q",
        result_type="image",
        source="tools/google_image_search.py",
    )
    web_action = SerpAction(
        tool_name="google_search",
        engine="google",
        label="Google Search",
        query_field="q",
        result_type="web",
        source="tools/google_search.py",
    )
    raw_action = SerpAction(
        tool_name="google_hotels_search",
        engine="google_hotels",
        label="Google Hotels Search",
        query_field="q",
        result_type="raw",
        source="tools/google_hotels_search.py",
    )

    assert normalize_action_payload(image_action, "coffee", {"images_results": [{"title": "A"}]})["results"][0][
        "title"
    ] == "A"
    assert normalize_action_payload(web_action, "coffee", {"organic_results": [{"title": "B"}]})["results"][0][
        "title"
    ] == "B"
    assert normalize_action_payload(raw_action, "hotel", {"hotels_results": []}) == {
        "query": "hotel",
        "engine": "google_hotels",
        "raw": {"hotels_results": []},
    }


def test_normalize_action_payload_exposes_raw_html_metadata():
    action = SerpAction(
        tool_name="google_hotels_search",
        engine="google_hotels",
        label="Google Hotels Search",
        query_field="q",
        result_type="raw",
        source="tools/google_hotels_search.py",
    )
    payload = {
        "code": 0,
        "task_id": "raw-task",
        "data": {
            "json": '{"hotels_results":[{"name":"Hotel A"}]}',
            "html": "<html><body><h1>Hotel A</h1></body></html>",
        },
    }

    result = normalize_action_payload(action, "hotel", payload)

    assert result["task_id"] == "raw-task"
    assert result["status_code"] == 0
    assert result["html"] == "<html><body><h1>Hotel A</h1></body></html>"
    assert result["html_preview"] == "Hotel A"
    assert result["data_json"] == {"hotels_results": [{"name": "Hotel A"}]}
    assert result["raw"] == payload
