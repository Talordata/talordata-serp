import importlib.util
from pathlib import Path

import yaml
from dify_plugin import Tool
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.plugin_registration import PluginRegistration

from scripts.generate_serp_tools import generated_tool_config
from utils.serp_action_registry import ACTIONS
from utils.serp_action_registry import get_action


def test_generated_tool_config_contains_schema_parameters():
    action = get_action("google_search")
    config = generated_tool_config(action)
    names = [param["name"] for param in config["parameters"]]

    assert config["identity"]["name"] == "google_search"
    assert config["extra"]["python"]["source"] == "tools/google_search.py"
    assert "q" in names
    assert "gl" in names
    assert "hl" in names
    assert "no_cache" not in names
    assert "params_json" not in names


def test_generated_tool_config_resolves_select_options_ref():
    action = get_action("google_search")
    config = generated_tool_config(action)
    params = {param["name"]: param for param in config["parameters"]}

    assert params["google_domain"]["options"][0]["value"] == "google.com"
    assert any(option["value"] == "us" for option in params["gl"]["options"])
    assert any(option["value"] == "en" for option in params["hl"]["options"])


def test_generated_tool_config_turns_tags_options_ref_into_selects():
    action = get_action("google_search")
    config = generated_tool_config(action)
    params = {param["name"]: param for param in config["parameters"]}

    assert params["cr"]["type"] == "select"
    assert any(option["value"] == "us" for option in params["cr"]["options"])
    assert params["lr"]["type"] == "select"
    assert any(option["value"] == "en" for option in params["lr"]["options"])


def test_generated_tool_config_adds_date_format_placeholder():
    action = get_action("google_image_search")
    config = generated_tool_config(action)
    params = {param["name"]: param for param in config["parameters"]}

    assert params["start_date"]["placeholder"] == {
        "en_US": "YYYY-MM-DD",
        "zh_Hans": "YYYY-MM-DD",
    }
    assert params["end_date"]["placeholder"] == {
        "en_US": "YYYY-MM-DD",
        "zh_Hans": "YYYY-MM-DD",
    }
    assert "YYYY-MM-DD" in params["start_date"]["human_description"]["en_US"]
    assert "YYYY-MM-DD" in params["end_date"]["human_description"]["zh_Hans"]


def test_search_tool_yamls_do_not_expose_params_json():
    for action in ACTIONS:
        config = yaml.safe_load(Path(f"tools/{action.tool_name}.yaml").read_text(encoding="utf-8"))
        names = [param["name"] for param in config["parameters"]]

        assert "params_json" not in names, action.tool_name


def test_search_tool_yamls_do_not_expose_no_cache():
    for action in ACTIONS:
        config = yaml.safe_load(Path(f"tools/{action.tool_name}.yaml").read_text(encoding="utf-8"))
        names = [param["name"] for param in config["parameters"]]

        assert "no_cache" not in names, action.tool_name


def test_generated_files_are_registered_in_provider():
    provider = yaml.safe_load(Path("provider/talordata_serp.yaml").read_text(encoding="utf-8"))
    registered = set(provider["tools"])

    for action in ACTIONS:
        assert f"tools/{action.tool_name}.yaml" in registered

    assert "tools/raw_serp_request.yaml" in registered


def test_generated_wrapper_exposes_single_tool_subclass():
    action = get_action("google_search")
    spec = importlib.util.spec_from_file_location("tools.google_search", action.source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    subclasses = [
        value for value in vars(module).values() if isinstance(value, type) and value != Tool and issubclass(value, Tool)
    ]

    assert len(subclasses) == 1
    assert subclasses[0].__name__ == "GoogleSearchTool"


def test_plugin_registration_loads_generated_tools():
    registration = PluginRegistration(DifyPluginEnv())
    registration._resolve_tool_providers()

    _, _, tools = registration.tools_mapping["talordata_serp"]

    assert len(tools) == len(ACTIONS) + 1
    assert "google_search" in tools
    assert "bing_image_search" in tools
    assert "raw_serp_request" in tools
