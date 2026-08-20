from __future__ import annotations

import json
import re
from typing import Any

from utils.serp_content_parser import (
    extract_structured_results,
    merge_result_sets,
    parse_html_results,
    parse_markdown_results,
)


def normalize_image_results(query: str, engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_payload(payload)
    source = unwrapped["data_json"] if isinstance(unwrapped["data_json"], dict) else payload
    source_items = _first_list(source, ("images_results", "inline_images", "image_results"))
    results = []
    for item in source_items:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": _text(item, "title", "name"),
                "link": _text(item, "link", "source_link", "original_context_url"),
                "image_url": _text(item, "original", "image", "image_url", "thumbnail"),
                "thumbnail_url": _text(item, "thumbnail", "thumbnail_url", "image"),
                "source": _text(item, "source", "domain"),
            }
        )

    return {
        "query": query,
        "engine": engine,
        "results": results,
        **response_metadata(unwrapped),
        "raw": payload,
    }


def normalize_web_results(query: str, engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_payload(payload)
    failure = _business_failure_message(
        unwrapped.get("content_text") or unwrapped.get("markdown")
    )
    parse_format = "unknown"
    recognized = False
    results: list[dict[str, Any]] = []

    if not failure:
        structured_source = unwrapped.get("structured")
        results, recognized = extract_structured_results(structured_source)
        if recognized:
            parse_format = "structured"

        if not results and isinstance(unwrapped.get("data_json"), dict):
            json_results, json_recognized = extract_structured_results(unwrapped["data_json"])
            if json_recognized:
                results = json_results
                recognized = True
                parse_format = "json"

        markdown = unwrapped.get("markdown") or ""
        html = unwrapped.get("html") or ""
        markdown_results = parse_markdown_results(markdown)
        html_results = parse_html_results(html)
        if markdown and html:
            results = merge_result_sets(markdown_results, html_results)
            recognized = True
            parse_format = "markdown+html"
        elif markdown:
            results = markdown_results
            recognized = True
            parse_format = "markdown"
        elif html and not results:
            results = html_results
            recognized = True
            parse_format = "html"

    parse_status = "failed" if failure else "parsed" if results else "empty" if recognized else "failed"

    return {
        "query": query,
        "engine": engine,
        "results": results,
        "parse_format": parse_format,
        "parse_status": parse_status,
        "parse_error": failure,
        **response_metadata(unwrapped),
        "raw": payload,
    }


def normalize_raw_payload(query: str, engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_payload(payload)
    result = {
        "query": query,
        "engine": engine,
        **response_metadata(unwrapped, include_data_json=True),
        "raw": payload,
    }
    return result


def unwrap_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    html = ""
    markdown = ""
    data_json: Any = None
    structured: Any = payload
    content_text = ""
    task_id = payload.get("task_id") if isinstance(payload, dict) else None

    if isinstance(data, dict):
        task_id = data.get("task_id") or task_id
        result = data.get("result")
        if isinstance(result, dict):
            structured = result
            html = _string(result.get("html") or data.get("html"))
            markdown = _string(result.get("markdown") or data.get("markdown"))
            data_json = _parse_data_json(result.get("json")) or _parse_data_json(data.get("json"))
        elif isinstance(result, str):
            content_text = result
            if _is_html_text(result):
                html = result
            else:
                parsed_result = _parse_data_json(result)
                if parsed_result is not None:
                    data_json = parsed_result
                else:
                    markdown = result
        else:
            structured = data
            html = _string(data.get("html"))
            markdown = _string(data.get("markdown"))
            data_json = _parse_data_json(data.get("json"))
    elif isinstance(data, str):
        content_text = data
        if _is_html_text(data):
            html = data
        else:
            parsed_data = _parse_data_json(data)
            if parsed_data is not None:
                data_json = parsed_data
            else:
                markdown = data

    return {
        "status_code": payload.get("code") if isinstance(payload, dict) else None,
        "task_id": task_id,
        "html": html,
        "html_preview": html_preview(html),
        "markdown": markdown,
        "data_json": data_json,
        "structured": structured,
        "content_text": content_text,
    }


def response_metadata(unwrapped: dict[str, Any], include_data_json: bool = False) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in ("status_code", "task_id", "html", "html_preview"):
        value = unwrapped.get(key)
        if value not in (None, ""):
            metadata[key] = value
    if include_data_json and unwrapped.get("data_json") not in (None, ""):
        metadata["data_json"] = unwrapped["data_json"]
    return metadata


def html_preview(html: str, max_length: int = 500) -> str:
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length]


def _first_list(payload: dict[str, Any], keys: tuple[str, ...]) -> list[Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return str(value)
    return ""


def _parse_data_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _business_failure_message(value: Any, max_length: int = 500) -> str:
    raw = str(value or "").strip()
    text = " ".join(raw.split())
    if not text or len(text) > max_length:
        return ""
    if _is_html_text(raw) or re.search(r"(?m)^\s*(?:#{1,6}\s|[-*+]\s)", raw):
        return ""
    lowered = text.lower()
    if lowered.startswith("error") or re.search(r"\b(?:failed|not found)\b", lowered):
        return text
    return ""


def _is_html_text(value: str) -> bool:
    lowered = str(value or "").lstrip().lower()
    return lowered.startswith("<!doctype html") or lowered.startswith("<html")
