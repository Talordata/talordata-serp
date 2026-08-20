from pathlib import Path

import yaml


GOOGLE_SEARCH_SCHEMA = (
    Path(__file__).resolve().parents[1] / "tools" / "google_search.yaml"
)


def test_google_search_exposes_optional_numeric_output_format():
    schema = yaml.safe_load(GOOGLE_SEARCH_SCHEMA.read_text(encoding="utf-8"))
    parameter = next(
        item for item in schema["parameters"] if item["name"] == "json"
    )

    assert parameter["type"] == "number"
    assert parameter["required"] is False
    assert parameter["label"]["en_US"] == "Output Format"
    assert parameter["default"] == 1
    assert "options" not in parameter
