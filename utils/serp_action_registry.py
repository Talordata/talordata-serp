from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SerpAction:
    tool_name: str
    engine: str
    label: str
    query_field: str
    result_type: str
    source: str


ACTIONS: tuple[SerpAction, ...] = (
    SerpAction("google_search", "google", "Google Search", "q", "web", "tools/google_search.py"),
    SerpAction("google_ai_mode_search", "google_ai_mode", "Google AI Mode Search", "q", "raw", "tools/google_ai_mode_search.py"),
    SerpAction("google_finance_search", "google_finance", "Google Finance Search", "q", "raw", "tools/google_finance_search.py"),
    SerpAction(
        "google_finance_markets_search",
        "google_finance_markets",
        "Google Finance Markets Search",
        "trend",
        "raw",
        "tools/google_finance_markets_search.py",
    ),
    SerpAction("google_flights_search", "google_flights", "Google Flights Search", "q", "raw", "tools/google_flights_search.py"),
    SerpAction("google_hotels_search", "google_hotels", "Google Hotels Search", "q", "raw", "tools/google_hotels_search.py"),
    SerpAction("google_image_search", "google_images", "Google Images Search", "q", "image", "tools/google_image_search.py"),
    SerpAction("google_jobs_search", "google_jobs", "Google Jobs Search", "q", "raw", "tools/google_jobs_search.py"),
    SerpAction("google_lens_search", "google_lens", "Google Lens Search", "url", "image", "tools/google_lens_search.py"),
    SerpAction("google_local_search", "google_local", "Google Local Search", "q", "raw", "tools/google_local_search.py"),
    SerpAction("google_maps_search", "google_maps", "Google Maps Search", "q", "raw", "tools/google_maps_search.py"),
    SerpAction("google_news_search", "google_news", "Google News Search", "q", "web", "tools/google_news_search.py"),
    SerpAction("google_patents_search", "google_patents", "Google Patents Search", "q", "raw", "tools/google_patents_search.py"),
    SerpAction(
        "google_patents_details_search",
        "google_patents_details",
        "Google Patents Details Search",
        "patent_id",
        "raw",
        "tools/google_patents_details_search.py",
    ),
    SerpAction("google_play_search", "google_play", "Google Play Search", "q", "raw", "tools/google_play_search.py"),
    SerpAction(
        "google_play_books_search",
        "google_play_books",
        "Google Play Books Search",
        "q",
        "raw",
        "tools/google_play_books_search.py",
    ),
    SerpAction(
        "google_play_games_search",
        "google_play_games",
        "Google Play Games Search",
        "q",
        "raw",
        "tools/google_play_games_search.py",
    ),
    SerpAction(
        "google_play_movies_search",
        "google_play_movies",
        "Google Play Movies Search",
        "q",
        "raw",
        "tools/google_play_movies_search.py",
    ),
    SerpAction(
        "google_play_product_search",
        "google_play_product",
        "Google Play Product Search",
        "product_id",
        "raw",
        "tools/google_play_product_search.py",
    ),
    SerpAction("google_scholar_search", "google_scholar", "Google Scholar Search", "q", "web", "tools/google_scholar_search.py"),
    SerpAction(
        "google_scholar_author_search",
        "google_scholar_author",
        "Google Scholar Author Search",
        "author_id",
        "raw",
        "tools/google_scholar_author_search.py",
    ),
    SerpAction(
        "google_scholar_cite_search",
        "google_scholar_cite",
        "Google Scholar Cite Search",
        "q",
        "raw",
        "tools/google_scholar_cite_search.py",
    ),
    SerpAction("google_shopping_search", "google_shopping", "Google Shopping Search", "q", "raw", "tools/google_shopping_search.py"),
    SerpAction("google_trends_search", "google_trends", "Google Trends Search", "q", "raw", "tools/google_trends_search.py"),
    SerpAction("google_videos_search", "google_videos", "Google Videos Search", "q", "web", "tools/google_videos_search.py"),
    SerpAction("google_web_search", "google_web", "Google Web Search", "q", "web", "tools/google_web_search.py"),
    SerpAction("bing_search", "bing", "Bing Search", "q", "web", "tools/bing_search.py"),
    SerpAction("bing_image_search", "bing_images", "Bing Image Search", "q", "image", "tools/bing_image_search.py"),
    SerpAction("bing_maps_search", "bing_maps", "Bing Maps Search", "q", "raw", "tools/bing_maps_search.py"),
    SerpAction("bing_news_search", "bing_news", "Bing News Search", "q", "web", "tools/bing_news_search.py"),
    SerpAction(
        "bing_shopping_search",
        "bing_shopping",
        "Bing Shopping Search",
        "q",
        "raw",
        "tools/bing_shopping_search.py",
    ),
    SerpAction("bing_videos_search", "bing_videos", "Bing Videos Search", "q", "web", "tools/bing_videos_search.py"),
    SerpAction("yandex_search", "yandex", "Yandex Search", "text", "web", "tools/yandex_search.py"),
    SerpAction("duckduckgo_search", "duckduckgo", "Duckduckgo Search", "q", "web", "tools/duckduckgo_search.py"),
)

ACTIONS_BY_TOOL = {action.tool_name: action for action in ACTIONS}


def get_action(tool_name: str) -> SerpAction:
    return ACTIONS_BY_TOOL[tool_name]
