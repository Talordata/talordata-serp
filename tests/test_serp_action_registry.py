from pathlib import Path

import yaml

from utils.serp_action_registry import ACTIONS
from utils.serp_action_registry import ACTIONS_BY_TOOL
from utils.serp_action_registry import get_action


SEARCH_PROVIDER_ORDER = ("google", "bing", "yandex", "duckduckgo")


def provider_group(tool_name):
    for index, prefix in enumerate(SEARCH_PROVIDER_ORDER):
        if tool_name.startswith(f"{prefix}_"):
            return index
    return len(SEARCH_PROVIDER_ORDER)


def test_registry_includes_enabled_schema_engines():
    engines = {action.engine for action in ACTIONS}

    assert "google" in engines
    assert "google_images" in engines
    assert "bing" in engines
    assert "bing_images" in engines
    assert "duckduckgo" in engines
    assert "yandex" in engines
    assert "google_product" not in engines


def test_registry_uses_stable_tool_names():
    assert get_action("google_search").engine == "google"
    assert get_action("google_image_search").engine == "google_images"
    assert get_action("bing_search").engine == "bing"
    assert get_action("bing_image_search").engine == "bing_images"


def test_registry_has_unique_tool_names_and_sources():
    names = [action.tool_name for action in ACTIONS]
    sources = [action.source for action in ACTIONS]

    assert len(names) == len(set(names))
    assert len(sources) == len(set(sources))
    assert set(ACTIONS_BY_TOOL) == set(names)


def test_registry_and_provider_tools_keep_search_provider_order():
    registry_tools = [action.tool_name for action in ACTIONS]
    provider = yaml.safe_load(Path("provider/talordata_serp.yaml").read_text(encoding="utf-8"))
    provider_tools = [
        Path(tool_path).stem for tool_path in provider["tools"] if tool_path != "tools/raw_serp_request.yaml"
    ]

    expected_group_order = sorted(provider_group(tool_name) for tool_name in registry_tools)

    assert [provider_group(tool_name) for tool_name in registry_tools] == expected_group_order
    assert provider_tools == registry_tools
