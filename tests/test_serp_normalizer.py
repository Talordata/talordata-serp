import pytest

from utils.serp_normalizer import normalize_image_results, normalize_web_results


def test_normalize_image_results_supports_images_results():
    payload = {
        "images_results": [
            {
                "title": "Coffee beans",
                "link": "https://example.com/page",
                "thumbnail": "https://example.com/thumb.jpg",
                "original": "https://example.com/original.jpg",
                "source": "Example",
            }
        ]
    }

    result = normalize_image_results("coffee", "bing_images", payload)

    assert result["query"] == "coffee"
    assert result["engine"] == "bing_images"
    assert result["results"][0] == {
        "title": "Coffee beans",
        "link": "https://example.com/page",
        "image_url": "https://example.com/original.jpg",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "source": "Example",
    }
    assert result["raw"] == payload


def test_normalize_image_results_falls_back_to_inline_images():
    payload = {
        "inline_images": [
            {
                "title": "Latte",
                "link": "https://example.com/latte",
                "image": "https://example.com/latte.jpg",
            }
        ]
    }

    result = normalize_image_results("latte", "bing_images", payload)

    assert result["results"][0]["image_url"] == "https://example.com/latte.jpg"


def test_normalize_web_results_supports_organic_results():
    payload = {
        "organic_results": [
            {
                "title": "Coffee",
                "link": "https://example.com/coffee",
                "snippet": "Coffee article",
            }
        ]
    }

    result = normalize_web_results("coffee", "google", payload)

    assert result["results"][0] == {
        "position": 1,
        "title": "Coffee",
        "link": "https://example.com/coffee",
        "snippet": "Coffee article",
        "source": "example.com",
    }


def test_normalize_web_results_reads_nested_data_json_string():
    payload = {
        "code": 0,
        "task_id": "task-123",
        "data": {
            "json": '{"organic_results":[{"title":"Pizza","link":"https://example.com","snippet":"Pizza article"}]}',
            "html": "<html><head><title>Pizza Search</title></head><body>Pizza article</body></html>",
        },
    }

    result = normalize_web_results("pizza", "bing", payload)

    assert result["status_code"] == 0
    assert result["task_id"] == "task-123"
    assert result["html"].startswith("<html>")
    assert "Pizza Search" in result["html_preview"]
    assert result["results"][0] == {
        "position": 1,
        "title": "Pizza",
        "link": "https://example.com",
        "snippet": "Pizza article",
        "source": "example.com",
    }
    assert result["raw"] == payload


def test_normalize_web_results_reads_mode_1_result_organic():
    payload = {
        "code": 0,
        "data": {
            "task_id": "mode-1-task",
            "result": {
                "organic": [
                    {
                        "position": 3,
                        "title": "TalorData",
                        "link": "https://talordata.com/serp-api",
                        "description": "SERP API",
                    }
                ]
            },
        },
    }

    result = normalize_web_results("TalorData", "google", payload)

    assert result["parse_format"] == "structured"
    assert result["parse_status"] == "parsed"
    assert result["task_id"] == "mode-1-task"
    assert result["results"] == [
        {
            "position": 3,
            "title": "TalorData",
            "link": "https://talordata.com/serp-api",
            "snippet": "SERP API",
            "source": "talordata.com",
        }
    ]


def test_normalize_web_results_reads_mode_2_result_json():
    payload = {
        "code": 0,
        "data": {
            "task_id": "mode-2-task",
            "result": {
                "json": '{"organic":[{"position":2,"title":"Example","link":"https://example.com","description":"Result"}]}'
            },
        },
    }

    result = normalize_web_results("Example", "google", payload)

    assert result["parse_format"] == "json"
    assert result["parse_status"] == "parsed"
    assert result["results"][0]["position"] == 2
    assert result["results"][0]["snippet"] == "Result"


def test_normalize_web_results_reads_mode_3_html():
    payload = {
        "code": 0,
        "data": {
            "task_id": "mode-3-task",
            "result": "<html><body><div class='g'><a href='https://example.com'><h3>Example</h3></a><div class='VwiC3b'>Snippet</div></div></body></html>",
        },
    }

    result = normalize_web_results("Example", "google", payload)

    assert result["parse_format"] == "html"
    assert result["parse_status"] == "parsed"
    assert result["results"][0]["link"] == "https://example.com"


def test_normalize_web_results_reads_mode_6_markdown():
    payload = {
        "code": 0,
        "data": {
            "task_id": "mode-6-task",
            "result": {
                "markdown": "### Organic Results\n\n- position: 1\n- title: Example\n- link: https://example.com\n- snippet: Result"
            },
        },
    }

    result = normalize_web_results("Example", "google", payload)

    assert result["parse_format"] == "markdown"
    assert result["parse_status"] == "parsed"
    assert result["results"][0]["position"] == 1


def test_normalize_web_results_merges_mode_7_markdown_and_html():
    payload = {
        "code": 0,
        "data": {
            "task_id": "mode-7-task",
            "result": {
                "markdown": "### Organic Results\n\n- position: 1\n- title: Example\n- link: https://example.com",
                "html": "<html><body><div class='g'><a href='https://example.com'><h3>Example</h3></a><div class='VwiC3b'>HTML snippet</div></div></body></html>",
            },
        },
    }

    result = normalize_web_results("Example", "google", payload)

    assert result["parse_format"] == "markdown+html"
    assert result["parse_status"] == "parsed"
    assert result["results"][0]["snippet"] == "HTML snippet"


@pytest.mark.parametrize(
    "message",
    [
        "error, Collection failed",
        "md data retrieval failed",
        "JSON fetch failed: cos object not found",
        "request failed",
        "object not found",
    ],
)
def test_normalize_web_results_marks_short_business_failure(message):
    result = normalize_web_results("Example", "google", {"code": 0, "data": message})

    assert result["results"] == []
    assert result["parse_status"] == "failed"
    assert result["parse_error"] == message


def test_normalize_web_results_marks_failure_nested_in_markdown_field():
    message = "request failed"
    payload = {"code": 0, "data": {"result": {"markdown": message}}}

    result = normalize_web_results("Example", "google", payload)

    assert result["results"] == []
    assert result["parse_status"] == "failed"
    assert result["parse_error"] == message


def test_normalize_web_results_exposes_html_when_no_structured_results():
    payload = {
        "code": 0,
        "task_id": "task-456",
        "data": {
            "html": "<html><body><h1>Only HTML</h1><p>No parsed results.</p></body></html>",
        },
    }

    result = normalize_web_results("pizza", "bing", payload)

    assert result["results"] == []
    assert result["task_id"] == "task-456"
    assert result["status_code"] == 0
    assert result["html"].startswith("<html>")
    assert result["html_preview"] == "Only HTML No parsed results."


def test_normalize_image_results_reads_nested_data_json_object():
    payload = {
        "code": 0,
        "task_id": "img-task",
        "data": {
            "json": {
                "images_results": [
                    {
                        "title": "Pizza image",
                        "link": "https://example.com/page",
                        "original": "https://example.com/pizza.jpg",
                    }
                ]
            }
        },
    }

    result = normalize_image_results("pizza", "google_images", payload)

    assert result["task_id"] == "img-task"
    assert result["status_code"] == 0
    assert result["results"][0]["image_url"] == "https://example.com/pizza.jpg"
