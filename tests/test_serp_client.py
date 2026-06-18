from urllib.error import HTTPError

import pytest

from utils.serp_client import DEFAULT_SERP_ENDPOINT
from utils.serp_client import SerpApiError, SerpClient


ENDPOINT = "https://serpapi.talordata.net/serp/v1/request"


class FakeHttpResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body.encode("utf-8")


def test_default_serp_endpoint_uses_production_endpoint():
    assert DEFAULT_SERP_ENDPOINT == ENDPOINT


def test_serp_client_posts_form_encoded_request():
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeHttpResponse(200, '{"images_results": [{"title": "A", "link": "https://example.com/a.jpg"}]}')

    client = SerpClient(endpoint=ENDPOINT, api_key="sk_test", urlopen=fake_urlopen)
    result = client.request({"engine": "bing_images", "q": "coffee", "count": 3, "empty": ""})

    assert result == {"images_results": [{"title": "A", "link": "https://example.com/a.jpg"}]}
    request, timeout = calls[0]
    assert request.full_url == ENDPOINT
    assert request.headers["Authorization"] == "Bearer sk_test"
    assert request.headers["Origin"] == "dify"
    assert request.headers["User-agent"] == "Talordata-Dify-Plugin/0.1.7"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["Content-type"] == "application/x-www-form-urlencoded"
    assert request.data == b"engine=bing_images&q=coffee&count=3&json=2&isjson=1"
    assert timeout == 60


def test_serp_client_rejects_empty_api_key():
    with pytest.raises(ValueError, match="SERP API key is required"):
        SerpClient(endpoint=ENDPOINT, api_key="")


def test_serp_client_raises_api_error_for_non_2xx():
    def fake_urlopen(request, timeout):
        raise HTTPError(ENDPOINT, 401, "Unauthorized", {}, None)

    client = SerpClient(endpoint=ENDPOINT, api_key="sk_bad", urlopen=fake_urlopen)

    with pytest.raises(SerpApiError) as exc:
        client.request({"engine": "bing_images", "q": "coffee"})

    assert exc.value.status_code == 401
    assert "Unauthorized" in str(exc.value)


def test_serp_client_raises_api_error_for_business_error_payload():
    def fake_urlopen(request, timeout):
        return FakeHttpResponse(200, '{"code": 401, "data": "API key authentication failed:error-6"}')

    client = SerpClient(endpoint=ENDPOINT, api_key="abc123", urlopen=fake_urlopen)

    with pytest.raises(SerpApiError) as exc:
        client.request({"engine": "bing_images", "q": "dify"})

    assert exc.value.status_code == 401
    assert "API key authentication failed" in str(exc.value)


def test_serp_client_reports_non_json_response_preview():
    def fake_urlopen(request, timeout):
        return FakeHttpResponse(502, "<html><body>Bad Gateway from proxy</body></html>")

    client = SerpClient(endpoint=ENDPOINT, api_key="abc123", urlopen=fake_urlopen)

    with pytest.raises(SerpApiError) as exc:
        client.request({"engine": "google", "q": "coffee"})

    assert exc.value.status_code == 502
    assert "SERP API returned invalid JSON" in str(exc.value)
    assert "Bad Gateway from proxy" in str(exc.value)
