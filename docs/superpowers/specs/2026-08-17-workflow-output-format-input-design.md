# Workflow Output Format Input Design

## Goal

Expose the TalorData Google SERP `json` request parameter in the first workflow form as `Output Format`, display `1` as the workflow default, and pass every supplied numeric value through unchanged.

## User Interface

- Add a start-node numeric input with label `Output Format` and variable name `output_format`.
- Set its displayed default to numeric value `1`.
- Keep the field optional. An omitted or blank value is not replaced by the workflow; the plugin client supplies its existing `json=1` default.
- Do not expose the implementation name `json` in the workflow form.

## Data Flow

1. The start node supplies `output_format` to `Validate and Build Search Tasks`.
2. The Prepare node preserves a supplied numeric value without applying an allowlist or substituting another value.
3. The preserved value is stored in the workflow config and every paginated search task as `output_format`.
4. The Google Search tool node maps the task value to the plugin parameter named `json`.
5. The plugin passes an explicit value through unchanged. If the value is omitted or blank, the existing client fallback supplies `json=1`.

## Plugin Contract

- Add an optional numeric `json` parameter to the Google Search tool schema.
- Label it `Output Format`, default it to `1`, and do not constrain it to an enumerated set of values.
- Bump the plugin package version from `0.1.11` to `0.1.12` so Dify does not reuse the old schema from cache.
- Rebuild `talordata-serp.difypkg` and update the workflow package dependency identifier to the new version and content checksum.

## Tests

- Verify the start node exposes `Output Format` with default `1`.
- Verify an omitted or blank value remains absent through the workflow and becomes `json=1` only in the plugin client.
- Verify explicit values, including a value outside `1`, `2`, `3`, `6`, and `7`, reach config, tasks, the Google tool binding, and the encoded request unchanged.
- Verify the plugin schema exposes `json` with default `1` and explicit overrides remain unchanged in the encoded request.
- Parse the final workflow YAML and verify its package dependency matches the rebuilt package.

## Out of Scope

- Changing the workflow's default LLM.
- Adding output-format controls to non-Google tools.
- Validating or interpreting output-format values in the workflow.
- Changing how returned formats are parsed after collection.
