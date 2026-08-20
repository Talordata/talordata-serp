from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag
from markdown_it import MarkdownIt


RESULT_LIST_KEYS = ("organic_results", "organic", "results")
CONTAINER_KEYS = ("data", "result", "json")
GOOGLE_HOSTS = ("google.com", "googleusercontent.com", "gstatic.com")
SNIPPET_SELECTORS = (".VwiC3b", ".aCOpRe", ".IsZvec", "[data-sncf]")


def normalize_result_records(items: list[Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    indexes: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        title = _first_text(item, "title", "name")
        link = normalize_external_url(_first_text(item, "link", "url"))
        if not title or not link:
            continue
        position = _positive_int(item.get("position")) or _positive_int(item.get("rank"))
        record = {
            "position": position or len(results) + 1,
            "title": title,
            "link": link,
            "snippet": _first_text(item, "snippet", "description", "summary"),
            "source": _first_text(item, "source", "domain") or _hostname(link),
        }
        key = _url_key(link)
        existing_index = indexes.get(key)
        if existing_index is None:
            indexes[key] = len(results)
            results.append(record)
        else:
            results[existing_index] = _enrich_record(results[existing_index], record)
    return results


def extract_structured_results(payload: Any) -> tuple[list[dict[str, Any]], bool]:
    queue = [payload]
    seen: set[int] = set()
    recognized = False
    while queue:
        current = queue.pop(0)
        if not isinstance(current, dict) or id(current) in seen:
            continue
        seen.add(id(current))
        for key in RESULT_LIST_KEYS:
            value = current.get(key)
            if isinstance(value, list):
                recognized = True
                results = normalize_result_records(value)
                if results or not value:
                    return results, True
        for key in CONTAINER_KEYS:
            value = current.get(key)
            if isinstance(value, dict):
                queue.append(value)
    return [], recognized


def parse_html_results(html: str) -> list[dict[str, Any]]:
    if not _looks_like_html(html):
        return []
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[dict[str, Any]] = []
    for anchor in soup.select("a:has(h3)"):
        heading = anchor.find("h3")
        if not isinstance(heading, Tag):
            continue
        link = normalize_external_url(anchor.get("href"))
        title = _clean_text(heading.get_text(" ", strip=True))
        if not title or not link:
            continue
        container = _result_container(anchor)
        snippet = ""
        if container is not None:
            for selector in SNIPPET_SELECTORS:
                snippet_node = container.select_one(selector)
                if isinstance(snippet_node, Tag):
                    snippet = _clean_text(snippet_node.get_text(" ", strip=True))
                    if snippet:
                        break
        candidates.append({"title": title, "link": link, "snippet": snippet})
    return normalize_result_records(candidates)


def parse_markdown_results(markdown: str) -> list[dict[str, Any]]:
    if not _looks_like_markdown(markdown):
        return []
    tokens = MarkdownIt("commonmark").parse(markdown)
    organic_level: int | None = None
    in_organic = False
    current: dict[str, Any] = {}
    candidates: list[dict[str, Any]] = []
    index = 0

    def flush() -> None:
        nonlocal current
        if current.get("title") and current.get("link"):
            candidates.append(current)
        current = {}

    while index < len(tokens):
        token = tokens[index]
        if token.type == "heading_open" and index + 1 < len(tokens):
            level = _heading_level(token.tag)
            inline = tokens[index + 1]
            heading_text = _clean_text(inline.content)
            lowered_heading = heading_text.lower()
            is_organic_heading = lowered_heading == "organic" or (
                "organic" in lowered_heading and "result" in lowered_heading
            )
            if is_organic_heading:
                flush()
                in_organic = True
                organic_level = level
            elif in_organic and (_inline_link(inline) or _heading_result(heading_text)):
                flush()
                heading_link = _inline_link(inline)
                current = (
                    {
                        "title": _inline_link_text(inline),
                        "link": heading_link,
                    }
                    if heading_link
                    else _heading_result(heading_text)
                )
            elif in_organic and organic_level is not None and level <= organic_level:
                flush()
                in_organic = False
            elif in_organic:
                flush()
                link = _inline_link(inline)
                if link:
                    current = {"title": _inline_link_text(inline), "link": link}
            index += 1
        elif in_organic and token.type == "list_item_open":
            inline_tokens = []
            cursor = index + 1
            while cursor < len(tokens) and tokens[cursor].type != "list_item_close":
                if tokens[cursor].type == "inline":
                    inline_tokens.append(tokens[cursor])
                cursor += 1
            for inline in inline_tokens:
                key, value = _field_value(inline.content)
                if key == "position":
                    if current.get("link"):
                        flush()
                    current["position"] = _positive_int(value)
                elif key in {"title", "name"}:
                    current["title"] = value
                elif key in {"link", "url"}:
                    current["link"] = _inline_link(inline) or value
                elif key in {"snippet", "description", "summary"}:
                    current["snippet"] = value
                elif key in {"source", "domain"}:
                    current["source"] = value
                elif not key:
                    text = _clean_text(inline.content)
                    link = _inline_link(inline) or normalize_external_url(text)
                    if link and not current.get("link"):
                        current["link"] = link
                        current.setdefault("title", _inline_link_text(inline))
                    elif (
                        current.get("link")
                        and not current.get("snippet")
                        and not link
                        and not _ignored_markdown_field(text)
                    ):
                        current["snippet"] = text
            index = cursor
        elif in_organic and token.type == "inline" and current.get("link"):
            if not _field_value(token.content)[0] and not _inline_link(token):
                text = _clean_text(token.content)
                if text and text != current.get("title"):
                    current.setdefault("snippet", text)
        index += 1
    flush()
    return normalize_result_records(candidates)


def merge_result_sets(
    primary: list[dict[str, Any]],
    fallback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = normalize_result_records(primary)
    indexes = {_url_key(item["link"]): index for index, item in enumerate(merged)}
    for item in normalize_result_records(fallback):
        key = _url_key(item["link"])
        if key in indexes:
            index = indexes[key]
            merged[index] = _enrich_record(merged[index], item)
        else:
            indexes[key] = len(merged)
            merged.append(item)
    used_positions: set[int] = set()
    next_position = 1
    for item in merged:
        position = _positive_int(item.get("position"))
        if position is None or position in used_positions:
            while next_position in used_positions:
                next_position += 1
            position = next_position
        item["position"] = position
        used_positions.add(position)
    return merged


def normalize_external_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        if raw.startswith("/url?"):
            query = parse_qs(urlsplit(raw).query)
            raw = (query.get("q") or query.get("url") or [""])[0]
        parsed = urlsplit(raw)
        host = (parsed.hostname or "").lower().rstrip(".")
        if host and _is_google_host(host) and parsed.path == "/url":
            query = parse_qs(parsed.query)
            raw = (query.get("q") or query.get("url") or [""])[0]
            parsed = urlsplit(raw)
            host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except (TypeError, ValueError):
        return ""
    if parsed.scheme.lower() not in {"http", "https"} or not host or _is_google_host(host):
        return ""
    netloc = host
    if port and not (parsed.scheme.lower() == "http" and port == 80) and not (
        parsed.scheme.lower() == "https" and port == 443
    ):
        netloc = f"{host}:{port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "", parsed.query, ""))


def _result_container(anchor: Tag) -> Tag | None:
    current: Tag | None = anchor
    for _ in range(6):
        parent = current.parent if current is not None else None
        if not isinstance(parent, Tag):
            return current
        current = parent
        classes = set(current.get("class") or [])
        if "g" in classes or current.get("data-snhf") is not None:
            return current
    return current


def _inline_link(token: Any) -> str:
    for child in token.children or []:
        if child.type == "link_open":
            return normalize_external_url(child.attrGet("href"))
    return ""


def _inline_link_text(token: Any) -> str:
    collecting = False
    output: list[str] = []
    for child in token.children or []:
        if child.type == "link_open":
            collecting = True
        elif child.type == "link_close":
            collecting = False
        elif collecting and child.type in {"text", "code_inline"}:
            output.append(child.content)
    return _clean_text(" ".join(output))


def _field_value(value: str) -> tuple[str, str]:
    text = _clean_text(value)
    if ":" not in text:
        return "", text
    key, field_value = text.split(":", 1)
    normalized_key = key.strip().lower().replace(" ", "_")
    supported = {
        "position",
        "rank",
        "title",
        "name",
        "link",
        "url",
        "snippet",
        "description",
        "summary",
        "source",
        "domain",
    }
    if normalized_key not in supported:
        return "", text
    if normalized_key == "rank":
        normalized_key = "position"
    return normalized_key, field_value.strip()


def _heading_result(value: str) -> dict[str, Any]:
    text = _clean_text(value)
    if not text.endswith(")"):
        return {}
    link_start = text.rfind("(")
    if link_start < 1:
        return {}
    link = normalize_external_url(text[link_start + 1 : -1])
    if not link:
        return {}
    heading = text[:link_start].strip()
    position = None
    title = heading
    number, separator, remainder = heading.partition(".")
    if separator and number.isdigit():
        position = _positive_int(number)
        title = remainder.strip()
    if not title:
        return {}
    return {"position": position, "title": title, "link": link}


def _ignored_markdown_field(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("redirect_link:", "favicon:", "date:"))


def _looks_like_html(value: Any) -> bool:
    text = str(value or "").lstrip().lower()
    return text.startswith("<!doctype html") or text.startswith("<html") or "<h3" in text


def _looks_like_markdown(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and not _looks_like_html(text) and ("#" in text or "- " in text)


def _heading_level(tag: str) -> int:
    try:
        return int(tag[1:])
    except (TypeError, ValueError):
        return 6


def _enrich_record(primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = dict(primary)
    for key in ("title", "snippet", "source"):
        if not merged.get(key) and fallback.get(key):
            merged[key] = fallback[key]
    return merged


def _url_key(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def _is_google_host(host: str) -> bool:
    return any(host == item or host.endswith(f".{item}") for item in GOOGLE_HOSTS)


def _hostname(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _first_text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return _clean_text(value)
    return ""


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())
