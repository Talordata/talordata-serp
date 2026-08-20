# Workflow Output Format Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `Output Format` workflow input that displays `1` by default, passes every explicit numeric value to TalorData unchanged, and leaves the plugin's existing `json=1` fallback responsible for omitted values.

**Architecture:** Add the user-facing field to the Dify start node, carry it as `output_format` through Prepare and each iteration task, and bind it to the Google tool parameter `json`. Expose `json` in the plugin's Google tool schema, bump the package to `0.1.12`, rebuild it, and update both workflow plugin identifiers with an exact package identifier.

**Tech Stack:** Dify workflow DSL YAML, Python 3.12 embedded code, TalorData Dify plugin schema, pytest, PyYAML, ZIP-compatible `.difypkg` packaging.

---

### Task 1: Workflow Contract Tests

**Files:**
- Modify: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`
- Test: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`

- [ ] **Step 1: Add failing start-input and Prepare passthrough tests**

Add tests that locate `output_format` in the Start variables and assert this exact UI contract:

```python
assert output_format == {
    "label": "Output Format",
    "default": 1,
    "required": False,
    "type": "number",
    "variable": "output_format",
}
```

Extend `call_prepare()` with `"output_format": None`. Add a parametrized test for `None`, `1`, `7`, and `42` asserting that `config["output_format"]` and every task's `output_format` equal the supplied value without allowlisting or substitution.

- [ ] **Step 2: Add a failing tool-binding test**

Assert the Google tool node contains:

```python
assert tool["tool_parameters"]["json"] == {
    "type": "mixed",
    "value": "{{#node_search_iteration.item.output_format#}}",
}
```

Also assert the Prepare node has a variable selector from `node_start.output_format`.

- [ ] **Step 3: Run the exact tests and verify RED**

Run:

```powershell
rtk .\talordata-serp-main\.venv\Scripts\python.exe -m pytest tests\test_talordata_seo_visibility_workflow.py -k output_format -q
```

Expected: failures because the Start field, Prepare argument, task value, and tool binding do not exist.

### Task 2: Plugin Contract Tests

**Files:**
- Modify: `E:/a-new/talor/dify/talordata-serp-main/tests/test_serp_client.py`
- Create: `E:/a-new/talor/dify/talordata-serp-main/tests/test_google_search_schema.py`

- [ ] **Step 1: Add a failing Google schema test**

Load `tools/google_search.yaml` with PyYAML, locate the parameter named `json`, and assert:

```python
assert parameter["type"] == "number"
assert parameter["required"] is False
assert parameter["label"]["en_US"] == "Output Format"
assert parameter["default"] == 1
assert "options" not in parameter
```

- [ ] **Step 2: Retain request-level default and passthrough coverage**

Keep the existing `test_request_preserves_explicit_json_override` assertion for `json=7`. Add an arbitrary explicit value assertion using `json=42`, and retain the no-argument assertion that the encoded request contains `json=1&isjson=1`.

- [ ] **Step 3: Run plugin tests and verify RED**

Run:

```powershell
rtk .\.venv\Scripts\python.exe -m pytest tests\test_google_search_schema.py tests\test_serp_client.py -q
```

from `E:/a-new/talor/dify/talordata-serp-main`.

Expected: schema test fails because `google_search.yaml` does not yet expose `json`; existing client behavior remains green.

### Task 3: Minimal Workflow and Schema Implementation

**Files:**
- Modify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`
- Modify: `E:/a-new/talor/dify/talordata-serp-main/tools/google_search.yaml`

- [ ] **Step 1: Add the Start variable**

Add this variable after `Search Depth`:

```yaml
- label: Output Format
  default: 1
  required: false
  type: number
  variable: output_format
```

- [ ] **Step 2: Carry the value through Prepare**

Add `output_format: object = None` to the embedded `main()` signature, include `"output_format": output_format` in `config` and every generated task, and add the `node_start.output_format` variable selector. Do not parse, validate, enumerate, or replace the value.

- [ ] **Step 3: Bind the task value to the tool parameter**

Add `json` to both `tool_parameters` and `tool_configurations`:

```yaml
json:
  type: mixed
  value: '{{#node_search_iteration.item.output_format#}}'
```

Add a matching `paramSchemas` entry derived from the plugin schema so imported Dify UI metadata and runtime inputs agree.

- [ ] **Step 4: Expose the plugin parameter**

Add this optional parameter near the query parameter in `tools/google_search.yaml`:

```yaml
- name: json
  type: number
  required: false
  label:
    en_US: Output Format
    zh_Hans: Output Format
  human_description:
    en_US: TalorData response output format. Explicit numeric values are passed through unchanged.
    zh_Hans: TalorData response output format. Explicit numeric values are passed through unchanged.
  llm_description: TalorData response output format. Explicit numeric values are passed through unchanged.
  form: form
  default: 1
```

- [ ] **Step 5: Run targeted tests and verify GREEN**

Run both Task 1 and Task 2 commands. Expected: all selected tests pass.

### Task 4: Version, Package, and Workflow Binding

**Files:**
- Modify: `E:/a-new/talor/dify/talordata-serp-main/manifest.yaml`
- Replace: `E:/a-new/talor/dify/talordata-serp-main/talordata-serp.difypkg`
- Modify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`
- Modify: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`

- [ ] **Step 1: Bump both manifest version fields**

Change the top-level and `meta.version` values from `0.1.11` to `0.1.12`.

- [ ] **Step 2: Rebuild a clean package**

Use the explicit runtime entry list from the existing package and `.difyignore`. Exclude `.venv`, tests, docs, caches, temporary files, and credentials. Build a new ZIP-compatible `talordata-serp.difypkg` with root-level `manifest.yaml`, `tools/`, `utils/`, `provider/`, and `_assets/` entries.

- [ ] **Step 3: Resolve and apply the exact package identifier**

Derive `dify_content_checksum` using the same canonical package/install mechanism that produced the current identifier; do not substitute the raw ZIP SHA256 or guess. Construct `plugin_identifier = f"talordata/talordata_serp:0.1.12@{dify_content_checksum}"`, update the workflow dependency and tool node to that value, then update the test constant to the same identifier.

- [ ] **Step 4: Verify package contents and binding**

Assert the archive contains version `0.1.12` and the new Google `json` schema, contains no development or credential files, and that both workflow identifier locations match the packaged version/checksum.

### Task 5: Final Verification

**Files:**
- Verify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`
- Verify: `E:/a-new/talor/dify/talordata-serp-main/talordata-serp.difypkg`

- [ ] **Step 1: Run focused workflow tests**

```powershell
rtk .\talordata-serp-main\.venv\Scripts\python.exe -m pytest tests\test_multi_format_workflow_handoff.py tests\test_talordata_seo_visibility_workflow.py -k "output_format or talordata_dependency or talordata_tool_configuration" -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run the full plugin suite**

```powershell
rtk .\.venv\Scripts\python.exe -m pytest -q
```

Expected: all plugin tests pass.

- [ ] **Step 3: Parse YAML and inspect the package**

Load the workflow and Google schema with `yaml.safe_load`, list the package archive, and verify the three layers agree on `Output Format`, default `1`, variable `output_format`, plugin parameter `json`, and version `0.1.12`.

- [ ] **Step 4: Record residual test state honestly**

Run the workflow suite with `--tb=no`; distinguish the known historical Prepare/Normalize contract failures from any new output-format failure. Do not claim the full historical suite is green unless its exit code is zero.

This workspace is not a Git repository, so commit steps are intentionally omitted.
