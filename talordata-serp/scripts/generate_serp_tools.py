from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
SCHEMA_ROOT = WORKSPACE / "talor-pay-package-view" / "configs" / "serp_schemas"
ENGINE_ROOT = SCHEMA_ROOT / "engines"
DICT_ROOT = SCHEMA_ROOT / "dicts"
I18N_ROOT = SCHEMA_ROOT / "i18n"
DATE_FORMAT = "YYYY-MM-DD"
DATE_PLACEHOLDER = {"en_US": DATE_FORMAT, "zh_Hans": DATE_FORMAT}
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.serp_action_registry import ACTIONS
from utils.serp_action_registry import SerpAction


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_i18n(lang: str) -> dict[str, str]:
    path = I18N_ROOT / f"{lang}.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(key): str(value) for key, value in raw.items()}


def i18n_text(key: str | None, translations: dict[str, str], fallback: str) -> str:
    if key and key in translations:
        return translations[key]
    return fallback


def title_from_key(key: str) -> str:
    return key.replace("_", " ").title()


def schema_for(action: SerpAction) -> dict[str, Any]:
    return read_yaml(ENGINE_ROOT / f"{action.engine}.yaml")


def options_for_ref(options_ref: str) -> list[dict[str, Any]]:
    path = DICT_ROOT / f"{options_ref}.yaml"
    if not path.exists():
        return []
    options = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(options, list):
        return []
    return [option for option in options if isinstance(option, dict)]


def tool_parameter_type(field_type: str) -> str:
    return {
        "date": "string",
        "number": "number",
        "select": "select",
        "switch": "boolean",
        "tags": "string",
        "text": "string",
    }.get(field_type, "string")


def option_label(option: dict[str, Any]) -> dict[str, str]:
    label = option.get("label")
    if label in (None, ""):
        label = option.get("value", "")
    label = str(label)
    return {"en_US": label, "zh_Hans": label}


def with_date_format_hint(help_text: dict[str, str]) -> dict[str, str]:
    return {
        "en_US": f"{help_text['en_US']} Format: {DATE_FORMAT}.",
        "zh_Hans": f"{help_text['zh_Hans']} 格式：{DATE_FORMAT}。",
    }


def generated_parameter(field: dict[str, Any], en: dict[str, str], zh: dict[str, str]) -> dict[str, Any]:
    key = str(field["key"])
    label_fallback = title_from_key(key)
    label = {
        "en_US": i18n_text(field.get("label_key"), en, label_fallback),
        "zh_Hans": i18n_text(field.get("label_key"), zh, label_fallback),
    }
    help_text = {
        "en_US": i18n_text(field.get("help_key"), en, f"{label['en_US']} parameter."),
        "zh_Hans": i18n_text(field.get("help_key"), zh, f"{label['zh_Hans']} 参数。"),
    }
    parameter: dict[str, Any] = {
        "name": key,
        "type": tool_parameter_type(str(field.get("type") or "text")),
        "required": bool(field.get("required")),
        "label": label,
        "human_description": help_text,
        "llm_description": f"{label['en_US']} parameter for the SERP request.",
        "form": "form",
    }
    if field.get("type") == "date":
        parameter["placeholder"] = DATE_PLACEHOLDER
        parameter["human_description"] = with_date_format_hint(help_text)
        parameter["llm_description"] = f"{label['en_US']} parameter for the SERP request. Format: {DATE_FORMAT}."
    if "default_value" in field and field["default_value"] not in (None, [], {}):
        parameter["default"] = field["default_value"]
    for numeric_key in ("min", "max"):
        if numeric_key in field:
            parameter[numeric_key] = field[numeric_key]
    options = field.get("options")
    if not options and field.get("options_ref"):
        options = options_for_ref(str(field["options_ref"]))
    if isinstance(options, list) and options:
        parameter["options"] = [
            {"value": str(option.get("value", "")), "label": option_label(option)}
            for option in options
            if isinstance(option, dict)
        ]
        if field.get("type") == "tags":
            parameter["type"] = "select"
    if field.get("type") == "tags":
        if parameter["type"] == "select":
            parameter["human_description"] = {
                "en_US": f"Select one {label['en_US']} value.",
                "zh_Hans": f"选择一个 {label['zh_Hans']} 值。",
            }
            parameter["llm_description"] = f"Select one {label['en_US']} value."
        else:
            parameter["human_description"] = {
                "en_US": f"{label['en_US']} values, comma-separated.",
                "zh_Hans": f"{label['zh_Hans']}，多个值用英文逗号分隔。",
            }
            parameter["llm_description"] = f"{label['en_US']} values, comma-separated."
    return parameter


def generated_tool_config(action: SerpAction) -> dict[str, Any]:
    schema = schema_for(action)
    en = load_i18n("en")
    zh = load_i18n("zh-cn")
    parameters = []
    seen = set()
    for group in schema.get("groups") or []:
        for field in group.get("fields") or []:
            if not isinstance(field, dict) or "key" not in field:
                continue
            key = str(field["key"])
            if key in seen:
                continue
            seen.add(key)
            parameters.append(generated_parameter(field, en, zh))

    parameters.append(
        {
            "name": "params_json",
            "type": "string",
            "required": False,
            "label": {
                "en_US": "Extra Parameters JSON",
                "zh_Hans": "额外参数 JSON",
            },
            "human_description": {
                "en_US": 'Optional JSON object merged into the SERP request, for example {"num":10}.',
                "zh_Hans": '可选 JSON 对象，会合并到 SERP 请求中，例如 {"num":10}。',
            },
            "llm_description": "Optional JSON object of additional SERP request parameters.",
            "form": "llm",
        }
    )
    parameters = [parameter for parameter in parameters if parameter.get("name") != "params_json"]
    return {
        "identity": {
            "name": action.tool_name,
            "author": "talordata",
            "label": {
                "en_US": action.label,
                "zh_Hans": action.label,
            },
        },
        "description": {
            "human": {
                "en_US": f"Call the {action.engine} engine through Talordata SERP API.",
                "zh_Hans": f"通过 Talordata SERP API 调用 {action.engine} engine。",
            },
            "llm": f"Call Talordata SERP engine {action.engine} and return normalized or raw SERP results.",
        },
        "parameters": parameters,
        "extra": {
            "python": {
                "source": action.source,
            }
        },
    }


def wrapper_code(action: SerpAction) -> str:
    class_name = "".join(part.title() for part in action.tool_name.split("_")) + "Tool"
    return (
        "from tools.serp_action import make_tool_class\n\n\n"
        f"{class_name} = make_tool_class({action.tool_name!r})\n"
    )


def dump_yaml(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def update_provider_tools(actions: tuple[SerpAction, ...]) -> None:
    provider_path = ROOT / "provider" / "talordata_serp.yaml"
    provider = read_yaml(provider_path)
    provider["tools"] = [f"tools/{action.tool_name}.yaml" for action in actions] + ["tools/raw_serp_request.yaml"]
    dump_yaml(provider_path, provider)


def generate() -> None:
    tools_dir = ROOT / "tools"
    for action in ACTIONS:
        yaml_path = tools_dir / f"{action.tool_name}.yaml"
        if action.tool_name != "bing_image_search":
            dump_yaml(yaml_path, generated_tool_config(action))
            (tools_dir / f"{action.tool_name}.py").write_text(wrapper_code(action), encoding="utf-8")
    update_provider_tools(ACTIONS)


if __name__ == "__main__":
    generate()
