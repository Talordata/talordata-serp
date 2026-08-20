# AI Markdown Final Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make validated AI-generated Markdown the workflow's final SEO report, retain the deterministic report as a safe fallback, and verify the complete path for TalorData JSON modes 1, 2, 3, 6, and 7 with the supplied DeepSeek test connection.

**Architecture:** Keep the current normalized SERP report as the evidence authority. Align the LLM prompt with the existing strict Markdown validator, then reconnect `Validate and Build Result.main()` to `validate_markdown_analysis()` and fall back to `deterministic_markdown()` on any unsafe or inconsistent model output. Do not change the default `gpt-4o` model configuration or the plugin package.

**Tech Stack:** Dify workflow YAML, embedded Python 3, pytest, PyYAML, TalorData SERP plugin 0.1.11, DeepSeek OpenAI-compatible Chat Completions for external verification.

---

## File Map

- Modify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`
  - Align the LLM system prompt with the validator's exact Markdown contract.
  - Reconnect the final result entry point to the existing AI Markdown validator and deterministic fallback.
- Modify: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`
  - Add an explicit regression proving distinct valid AI briefs produce distinct final reports.
  - Reuse the existing prompt, safety, ranking, URL, and fallback tests.
- Verify only: `E:/a-new/talor/dify/tests/test_multi_format_workflow_handoff.py`
  - Confirm JSON modes still reach canonical AI input.
- Create temporarily, then delete: `E:/a-new/talor/dify/.tmp_deepseek_final_e2e.py`
  - Run real modes 1, 2, 3, 6, and 7 through the plugin, workflow, DeepSeek, validator, and final payload without persisting credentials or API responses.

The target project is not a Git repository, so commit steps are intentionally omitted.

### Task 1: Lock the AI-output regression in a failing test

**Files:**
- Modify: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`
- Test: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`

- [ ] **Step 1: Add a distinct-output regression test**

Add this test next to `test_build_wraps_valid_markdown_in_json_envelope`:

```python
def test_build_uses_each_distinct_valid_ai_markdown_output(dsl):
    first = valid_markdown_brief().strip()
    second = first.replace(
        "The target has a confirmed rank of 1 for coffee.",
        "The target has a confirmed rank of 1 for coffee, with a different evidence-backed summary.",
    )

    first_result = call_build(dsl, first)
    second_result = call_build(dsl, second)

    assert first_result["report_markdown"] == first
    assert second_result["report_markdown"] == second
    assert first_result["report_markdown"] != second_result["report_markdown"]
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```powershell
rtk ..\talordata-serp-main\.venv\Scripts\python.exe -m pytest test_talordata_seo_visibility_workflow.py::test_build_uses_each_distinct_valid_ai_markdown_output -q
```

Expected: FAIL because the current entry point ignores `analysis` and returns the same deterministic report for both inputs.

### Task 2: Align the LLM prompt with the Markdown validator

**Files:**
- Modify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml:10370`
- Test: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py:2557`

- [ ] **Step 1: Run the existing prompt-contract tests and verify RED**

Run:

```powershell
rtk ..\talordata-serp-main\.venv\Scripts\python.exe -m pytest test_talordata_seo_visibility_workflow.py::test_llm_contract_requests_markdown_industry_brief test_talordata_seo_visibility_workflow.py::test_llm_contract_requires_exact_empty_competitor_table_row -q
```

Expected: both tests FAIL because the prompt requests the newer narrative report structure instead of the validator's industry-brief tables.

- [ ] **Step 2: Replace the system prompt with the exact validator contract**

Keep the current evidence and prompt-injection rules, but require this exact title and ordered sections:

```markdown
# SEO Visibility Industry Brief

## Executive Summary
## Keyword Visibility
| Keyword | TalorData Performance | Page / Evidence | Priority | Recommended Action |
|---|---|---|---|---|

## Competitor Landscape
| Keyword | Competitor | Competitor Performance | Ahead of Target Site? | Competitor Page / Evidence |
|---|---|---|---|---|

## Priority Opportunities
### High
### Medium
### Low

## Recommended Actions
## Data Quality and Limitations
```

The prompt must also state all of the following literally:

```text
The response must begin immediately with # SEO Visibility Industry Brief
Never output <think> or </think>
Do not put explanatory prose in a table cell
When there is no direct parsed competitor evidence, output exactly this single data row and no other competitor data row:
| None | No competitor evidence | Insufficient data to determine ranking. | Not verified | None |
Do not paraphrase, expand, or replace any cell in that row.
```

Retain the exact incomplete-evidence sentence already required by the workflow and retain `temperature: 0.2` without introducing `max_tokens`.

- [ ] **Step 3: Run the prompt-contract tests and verify GREEN**

Run the command from Step 1.

Expected: `2 passed`.

### Task 3: Reconnect validated AI Markdown to the final result

**Files:**
- Modify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml:11837`
- Test: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py:2607`

- [ ] **Step 1: Replace only the final embedded `main()` implementation**

Use the existing helpers already defined in the node:

```python
def main(
    analysis,
    report: dict,
    allowed_keywords: list,
    allowed_evidence_links: list,
    config: dict,
    run_id: str,
    run_time: str,
) -> dict:
    if not isinstance(report, dict):
        raise ValueError("report must be an object")
    allowed_links = validated_allowed_links(allowed_evidence_links)
    allowed_link_set = set(allowed_links)
    markdown, adjusted = validate_markdown_analysis(
        analysis,
        report,
        allowed_keywords,
        allowed_link_set,
    )
    report_status = report.get("status")
    if markdown is None:
        markdown = deterministic_markdown(report, allowed_link_set)
        status = "failed" if report_status == "failed" else "partial"
    else:
        status = (
            "partial"
            if adjusted or report_status != "completed"
            else "completed"
        )
    result = {
        "status": status,
        "report_format": "markdown",
        "report_markdown": markdown,
    }
    if len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) >= 200000:
        result["status"] = "partial"
        result["report_markdown"] = deterministic_markdown(
            report,
            allowed_link_set,
        )
    return {"result": result}
```

Do not remove the legacy JSON helpers or the existing validators in this scoped fix.

- [ ] **Step 2: Run the new distinct-output test and verify GREEN**

Run the Task 1 Step 2 command.

Expected: `1 passed`.

- [ ] **Step 3: Run the Markdown acceptance and fallback regression group**

Run:

```powershell
rtk ..\talordata-serp-main\.venv\Scripts\python.exe -m pytest test_talordata_seo_visibility_workflow.py -q -k "llm_contract or build_wraps_valid_markdown or build_accepts_one_markdown_fence or build_accepts_one_leading_closed_think_block or build_accepts_closed_think_block_joined or build_rejects_unsafe_or_incomplete_think_output or build_falls_back_for_malformed_or_unsafe_markdown or build_fallback_includes_required_unparsed_organic_limitation or build_rejects_ranking_claim or build_rejects_invented or build_uses_deterministic_markdown_fallback or build_uses_each_distinct"
```

Expected: all selected tests PASS.

### Task 4: Run focused workflow regression tests

**Files:**
- Verify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`
- Test: `E:/a-new/talor/dify/tests/test_multi_format_workflow_handoff.py`
- Test: `E:/a-new/talor/dify/tests/test_talordata_seo_visibility_workflow.py`

- [ ] **Step 1: Parse the YAML and verify the model remains unchanged**

Run a PyYAML check that asserts the app name, 32 nodes, and `node_llm_analysis.data.model` remains `gpt-4o` with provider `langgenius/openai/openai`.

Expected: exit 0.

- [ ] **Step 2: Run JSON-mode workflow handoff tests**

Run:

```powershell
rtk ..\talordata-serp-main\.venv\Scripts\python.exe -m pytest test_multi_format_workflow_handoff.py -q
```

Expected: all tests PASS.

- [ ] **Step 3: Run the complete workflow test module and classify unrelated drift**

Run:

```powershell
rtk ..\talordata-serp-main\.venv\Scripts\python.exe -m pytest test_talordata_seo_visibility_workflow.py -q
```

Expected: all AI Markdown tests PASS. If unrelated historical YAML/test drift remains, record exact failures rather than changing unrelated workflow behavior.

### Task 5: Run real DeepSeek end-to-end verification for every JSON mode

**Files:**
- Create temporarily: `E:/a-new/talor/dify/.tmp_deepseek_final_e2e.py`
- Read: `E:/a-new/talor/dify/deepseek.txt`
- Read: `E:/a-new/talor/dify/talordata-serp-main/talordata-serp.difypkg`
- Read: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`

- [ ] **Step 1: Build a credential-safe test harness**

The harness must:

```text
read DeepSeek base URL, model, and API key from deepseek.txt
read the TalorData token through getpass
load plugin code from a temporary extraction of talordata-serp.difypkg
execute node_prepare, plugin parameter construction, SerpClient, plugin normalization,
node_merge_search_result, node_normalize, the exact YAML LLM prompt, DeepSeek
/chat/completions, node_build_result, and node_build_webhook_payload
never print raw credentials, raw API responses, AI report bodies, or SERP bodies
```

- [ ] **Step 2: Run modes 1, 2, 3, 6, and 7**

For each mode assert:

```text
plugin parse_status == parsed
plugin results count > 0
workflow search_status == success
parsed_organic_count > 0
DeepSeek finish_reason == stop
DeepSeek Markdown passes validate_markdown_analysis
final report_markdown equals the validated DeepSeek Markdown
payload JSON round-trip equals the final result
```

Start with workflow-equivalent caching. If modes 6 or 7 return known missing-artifact errors, retry that mode with `no_cache=true` and report the upstream cache failure separately.

Expected: all five modes reach DeepSeek and use the validated AI Markdown in the final result.

### Task 6: Final safety and cleanup verification

**Files:**
- Verify: `E:/a-new/talor/dify/TalorData SEO Visibility Agent.yaml`
- Verify: `E:/a-new/talor/dify/talordata-serp-main/talordata-serp.difypkg`

- [ ] **Step 1: Scan temporary files for credential fragments before deletion**

Use `rg -l` with the known TalorData prefix and a masked DeepSeek prefix against temporary scripts and extraction directories. Expected: exit 1 with no matched filenames.

- [ ] **Step 2: Delete the exact temporary scripts and extraction directory**

Resolve each absolute temporary path first, then remove only those verified paths. Expected: no `.tmp_*` test artifacts remain.

- [ ] **Step 3: Confirm the plugin package is unchanged**

Run:

```powershell
rtk certutil -hashfile talordata-serp.difypkg SHA256
```

Expected SHA256:

```text
dec1fcdbe70640f4a880a52152e15aa9d16bf360d9bf3dc29a1dbd7c495eb167
```

- [ ] **Step 4: Report evidence and remaining risks**

Report per-mode parse format, result count, DeepSeek completion status, AI validation status, final status, whether the final report equals the validated AI report, any upstream cache retries, automated test counts, and any unrelated existing test failures.
