import pytest

from utils.serp_content_parser import (
    merge_result_sets,
    normalize_external_url,
    parse_html_results,
    parse_markdown_results,
)


GOOGLE_HTML = """
<!doctype html>
<html><body>
  <div id="search">
    <div class="g">
      <a href="/url?q=https%3A%2F%2Fexample.com%2Fcoffee%23section&sa=U"><h3>Example Coffee</h3></a>
      <div class="VwiC3b">A useful coffee guide.</div>
    </div>
    <div class="g">
      <a href="https://competitor.example/coffee"><h3>Competitor Coffee</h3></a>
    </div>
    <div class="g">
      <a href="https://example.com/coffee"><h3>Duplicate Coffee</h3></a>
    </div>
    <a href="/search?q=coffee+beans"><h3>More results</h3></a>
  </div>
</body></html>
"""


GOOGLE_MARKDOWN = """
# Google Search: coffee

### Search Information

- total_results: About 100 results
- query_displayed: coffee

### AI URL

- https://www.google.com/search?q=coffee&udm=50

### Organic Results

#### Result 1

- position: 1
- title: Example Coffee
- link: https://example.com/coffee
- snippet: Markdown summary

#### Result 2

- position: 2
- title: Competitor Coffee
- link: https://competitor.example/coffee

### Pagination

- [Next](https://www.google.com/search?q=coffee&start=10)
"""


def test_parse_html_results_extracts_ranked_organic_results():
    results = parse_html_results(GOOGLE_HTML)

    assert results == [
        {
            "position": 1,
            "title": "Example Coffee",
            "link": "https://example.com/coffee",
            "snippet": "A useful coffee guide.",
            "source": "example.com",
        },
        {
            "position": 2,
            "title": "Competitor Coffee",
            "link": "https://competitor.example/coffee",
            "snippet": "",
            "source": "competitor.example",
        },
    ]


def test_parse_markdown_results_reads_only_organic_section():
    results = parse_markdown_results(GOOGLE_MARKDOWN)

    assert results == [
        {
            "position": 1,
            "title": "Example Coffee",
            "link": "https://example.com/coffee",
            "snippet": "Markdown summary",
            "source": "example.com",
        },
        {
            "position": 2,
            "title": "Competitor Coffee",
            "link": "https://competitor.example/coffee",
            "snippet": "",
            "source": "competitor.example",
        },
    ]


def test_parse_markdown_results_supports_link_based_result_blocks():
    markdown = """
### Organic Results

#### [First result](https://first.example/page)

First result summary.

#### [Second result](https://second.example/page)
"""

    results = parse_markdown_results(markdown)

    assert [item["link"] for item in results] == [
        "https://first.example/page",
        "https://second.example/page",
    ]
    assert results[0]["snippet"] == "First result summary."


def test_parse_markdown_results_supports_real_mode_6_heading_format():
    markdown = """
# Google Search: TalorData SERP API

### Search Information
- organic_results_state: Results for exact spelling

### Organic

### 1.TalorData SERP API(https://peerlist.io/priest10739/project/talordata-serp-api)
- source: Peerlist
- https://peerlist.io/priest10739/project/talordata-serp-api
- TalorData provides structured search engine result data.
- redirect_link: https://www.google.com/url?url=https://peerlist.io/priest10739/project/talordata-serp-api
- favicon: data:image/png;base64,ignored

### 2.Talordata API(https://publicapi.dev/talordata-api)
- source: PublicAPI
- https://publicapi.dev/talordata-api
- Real-time structured SERP data.

### Pagination
- next: https://www.google.com/search?start=10
"""

    results = parse_markdown_results(markdown)

    assert results == [
        {
            "position": 1,
            "title": "TalorData SERP API",
            "link": "https://peerlist.io/priest10739/project/talordata-serp-api",
            "snippet": "TalorData provides structured search engine result data.",
            "source": "Peerlist",
        },
        {
            "position": 2,
            "title": "Talordata API",
            "link": "https://publicapi.dev/talordata-api",
            "snippet": "Real-time structured SERP data.",
            "source": "PublicAPI",
        },
    ]


def test_merge_result_sets_preserves_markdown_order_and_enriches_from_html():
    markdown_results = parse_markdown_results(GOOGLE_MARKDOWN)
    markdown_results[1]["snippet"] = ""
    html_results = parse_html_results(GOOGLE_HTML)
    html_results[1]["snippet"] = "HTML fallback summary"

    results = merge_result_sets(markdown_results, html_results)

    assert [item["link"] for item in results] == [
        "https://example.com/coffee",
        "https://competitor.example/coffee",
    ]
    assert results[0]["snippet"] == "Markdown summary"
    assert results[1]["snippet"] == "HTML fallback summary"
    assert [item["position"] for item in results] == [1, 2]


def test_merge_result_sets_preserves_explicit_source_positions():
    primary = [
        {
            "position": 11,
            "title": "Page eleven",
            "link": "https://example.com/eleven",
        }
    ]
    fallback = [
        {
            "position": 12,
            "title": "Page twelve",
            "link": "https://example.com/twelve",
        }
    ]

    results = merge_result_sets(primary, fallback)

    assert [item["position"] for item in results] == [11, 12]


def test_normalize_external_url_rejects_malformed_port():
    assert normalize_external_url("https://example.com:bad/path") == ""


@pytest.mark.parametrize(
    "value",
    [
        "error, Collection failed",
        "md data retrieval failed",
        "JSON fetch failed: cos object not found",
    ],
)
def test_short_business_failure_strings_are_not_html_or_markdown(value):
    assert parse_html_results(value) == []
    assert parse_markdown_results(value) == []
