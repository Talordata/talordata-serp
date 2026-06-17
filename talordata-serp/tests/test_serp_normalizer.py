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
        "title": "Coffee",
        "link": "https://example.com/coffee",
        "snippet": "Coffee article",
        "source": "",
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
        "title": "Pizza",
        "link": "https://example.com",
        "snippet": "Pizza article",
        "source": "",
    }
    assert result["raw"] == payload


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
