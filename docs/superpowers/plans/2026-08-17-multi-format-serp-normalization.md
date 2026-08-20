# Multi-format SERP Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse Talordata Google SERP responses for `json=1/2/3/6/7` into one ranked result schema and carry that evidence through the Dify workflow to `ai_input_json`.

**Architecture:** `utils/serp_normalizer.py` remains the public normalization entry point and delegates HTML/Markdown extraction to focused helpers in a new `utils/serp_content_parser.py`. The workflow consumes the plugin's canonical `results` first, retains narrow raw fallbacks for older packages, and propagates explicit parse failures instead of treating them as empty successful searches.

**Tech Stack:** Python 3.12, pytest, Beautiful Soup 4.15, markdown-it-py 4.2, PyYAML for workflow test loading, Dify plugin package format.

---

### Task 1: Add parser contract tests

**Files:**
- Create: `utils/serp_content_parser.py`
- Create: `tests/test_serp_content_parser.py`
- Modify: `tests/test_serp_normalizer.py`

- [ ] **Step 1: Write failing structured-response tests**

Add fixtures matching observed `data.result.organic` and `data.result.json` payloads. Assert both normalize to records containing `position`, `title`, `link`, `snippet`, and `source`, with `parse_status="parsed"` and the correct `parse_format`.

- [ ] **Step 2: Run structured tests and verify RED**

Run: `rtk .\.venv\Scripts\python.exe -m pytest tests\test_serp_normalizer.py -q`

Expected: FAIL because `data.result` is not unwrapped, position is omitted, and parse metadata does not exist.

- [ ] **Step 3: Write failing HTML parser tests**

Use a minimal Google HTML fixture with two natural result containers, one `/url?q=` redirect, a navigation link, duplicate URL, and missing snippet. Assert only two canonical ranked records are returned.

- [ ] **Step 4: Run HTML tests and verify RED**

Run: `rtk .\.venv\Scripts\python.exe -m pytest tests\test_serp_content_parser.py -q`

Expected: FAIL because `utils.serp_content_parser` does not yet exist.

- [ ] **Step 5: Write failing Markdown and mode 7 merge tests**

Use a CommonMark fixture with `Search Information`, `AI URL`, `Organic Results`, `Pagination`, and external result links. Assert metadata/navigation links are excluded. Add a mode 7 payload where Markdown supplies ordering and HTML supplies a missing snippet; assert URL-based deduplication and enrichment.

- [ ] **Step 6: Write failing business-failure tests**

Parameterize the observed short payloads `error, Collection failed`, `md data retrieval failed`, and `JSON fetch failed: cos object not found`. Assert `results=[]`, `parse_status="failed"`, and a bounded `parse_error`.

- [ ] **Step 7: Run all new tests and verify RED**

Run: `rtk .\.venv\Scripts\python.exe -m pytest tests\test_serp_content_parser.py tests\test_serp_normalizer.py -q`

Expected: FAIL only for the missing multi-format behavior.

### Task 2: Implement the canonical parsers

**Files:**
- Create: `utils/serp_content_parser.py`
- Modify: `utils/serp_normalizer.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add runtime parser dependencies**

Append:

```text
beautifulsoup4>=4.15.0,<5.0.0
markdown-it-py>=4.2.0,<5.0.0
```

- [ ] **Step 2: Implement URL and record canonicalization**

Create helpers that unwrap Google redirect links with `urllib.parse`, reject non-HTTP and Google navigation URLs, derive host names, validate title/link, preserve positive integer positions, assign missing positions in document order, and deduplicate by normalized URL.

- [ ] **Step 3: Implement structured extraction**

Traverse only `data`, `result`, and decoded `json` containers. Read result lists only from `organic_results`, `organic`, and `results`, and map the documented field aliases into canonical records.

- [ ] **Step 4: Implement HTML extraction**

Use `BeautifulSoup(html, "html.parser")`. Prefer result containers containing `a:has(h3)`; obtain the link/title from the heading anchor and snippet from the same nearest result container. Fall back to heading anchors when wrappers differ. Pass candidates through canonical URL filtering and deduplication.

- [ ] **Step 5: Implement Markdown AST extraction**

Use `MarkdownIt("commonmark").parse(markdown)`. Track heading sections, process link tokens only inside an organic-results section when present, exclude metadata/AI URL/pagination sections, and use adjacent paragraph text as the snippet.

- [ ] **Step 6: Implement mode 7 merging and failure metadata**

Make Markdown the ordering source, enrich matching records from HTML, append HTML-only records, and reassign stable positive positions. Detect short whole-payload error strings before parsing and expose `parse_format`, `parse_status`, and `parse_error`.

- [ ] **Step 7: Run parser tests and verify GREEN**

Run: `rtk .\.venv\Scripts\python.exe -m pytest tests\test_serp_content_parser.py tests\test_serp_normalizer.py -q`

Expected: PASS.

### Task 3: Preserve request defaults and action integration

**Files:**
- Modify: `tests/test_serp_client.py`
- Modify: `tests/test_serp_action.py`

- [ ] **Step 1: Add explicit-mode request tests**

Parameterize `json` values `1,2,3,6,7` and assert the form body preserves each explicit value while omitted `json` still produces `json=1`.

- [ ] **Step 2: Run request tests and verify behavior**

Run: `rtk .\.venv\Scripts\python.exe -m pytest tests\test_serp_client.py tests\test_serp_action.py -q`

Expected: PASS; if a regression is exposed, make only the minimal client/action fix and rerun.

### Task 4: Update and test workflow evidence handoff

**Files:**
- Modify: `E:\a-new\talor\dify\tests\test_talordata_seo_visibility_workflow.py`
- Modify: `E:\a-new\talor\dify\TalorData SEO Visibility Agent.yaml`

- [ ] **Step 1: Add failing Merge-node tests**

Extract the embedded `node_merge_search_result` Python and assert canonical plugin `results` are retained, `raw.data.result.organic` is a supported fallback, and `parse_status="failed"` produces `search_status="failed"` with the plugin error.

- [ ] **Step 2: Add failing Normalize-node integration tests**

Pass canonical ranked records from modes `1/2/3/6/7` through Merge and Normalize. Assert `ai_input_json` deserializes, evidence links exist, parsed counts are nonzero, and target/competitor rankings come from the supplied positions.

- [ ] **Step 3: Run workflow tests and verify RED**

Run: `rtk .\talordata-serp-main\.venv\Scripts\python.exe -m pytest tests\test_talordata_seo_visibility_workflow.py -q`

Working directory: `E:\a-new\talor\dify`

Expected: FAIL for direct mode 1 fallback and failure propagation.

- [ ] **Step 4: Modify only the Merge code block**

Add `parse_format`, `parse_status`, and `parse_error` to compact response keys. Prefer canonical `results`; extend raw extraction to direct `result.organic` and embedded `result.json`; set failed status when the plugin reports `parse_status="failed"`.

- [ ] **Step 5: Run workflow tests and verify GREEN**

Run the Task 4 Step 3 command again.

Expected: PASS.

### Task 5: Version, package, and static verification

**Files:**
- Modify: `manifest.yaml`
- Modify: `utils/serp_client.py`
- Replace: `talordata-serp.difypkg`
- Inspect/conditionally modify: `E:\a-new\talor\dify\TalorData SEO Visibility Agent.yaml`

- [ ] **Step 1: Bump plugin version to 0.1.11**

Set both manifest version fields and the HTTP `User-Agent` to `0.1.11`. Update their existing tests first if they assert the old version.

- [ ] **Step 2: Install new dependencies into the local test environment**

Run: `rtk .\.venv\Scripts\python.exe -m pip install -r requirements.txt`

Expected: dependency resolution succeeds on Python 3.12.

- [ ] **Step 3: Run the focused and full plugin suites**

Run: `rtk .\.venv\Scripts\python.exe -m pytest tests\test_serp_client.py tests\test_serp_content_parser.py tests\test_serp_normalizer.py tests\test_serp_action.py -q`

Then: `rtk .\.venv\Scripts\python.exe -m pytest -q`

Expected: focused tests pass. Record any unrelated pre-existing full-suite failures with exact paths.

- [ ] **Step 4: Build a clean Dify package**

Use the installed Dify plugin CLI packaging command if available and confirm `.difyignore` excludes virtual environments, tests, temporary probes, and docs. If the CLI is unavailable, rebuild the ZIP-compatible `.difypkg` from the explicit runtime file set rather than editing the old archive that contains `.venv312`.

- [ ] **Step 5: Verify package contents**

Confirm the archive contains `manifest.yaml`, `requirements.txt`, updated `utils/serp_client.py`, `utils/serp_normalizer.py`, and `utils/serp_content_parser.py`, and contains no token, `.venv`, test cache, or temporary files.

- [ ] **Step 6: Resolve workflow plugin identifier without guessing**

Compare the package hash with Dify's identifier rules or an identifier emitted by the package/install tooling. Update both workflow identifier locations only when the exact full identifier is known; otherwise leave the old identifier intact and report that Dify must rebind the installed local `0.1.11` package.

### Task 6: Real API end-to-end verification

**Files:**
- Create temporarily, then delete: `.tmp_verify_json_modes.py`

- [ ] **Step 1: Build a secure real-response harness**

Read the token with `getpass`, use the current `SerpClient` parameter construction and a Windows Schannel curl adapter, and load the exact Merge/Normalize code blocks from the workflow YAML. Do not write response bodies or credentials to disk.

- [ ] **Step 2: Test modes 1, 2, 3, 6, and 7**

For each explicit mode, report raw shape, plugin `parse_format`/`parse_status`, normalized result count, workflow parsed count, evidence-link count, and whether `ai_input_json` deserializes. Use bounded retries only for transient mode 6/7 collection failures.

- [ ] **Step 3: Verify default mode separately**

Send one request with no explicit `json` and confirm the request body and response shape match mode 1 behavior.

- [ ] **Step 4: Remove the temporary harness and scan for secrets**

Delete the probe with `apply_patch`; search project/workflow files for the supplied token and temporary filenames. Confirm no credential or raw response was persisted.

- [ ] **Step 5: Record honest acceptance status**

Mark a mode successful only when a successful content payload produces ranked canonical results and valid AI input. When the API returns a known failure string, record that failure propagation passed but content parsing could not be live-verified in that attempt.

### Task 7: Final review

**Files:**
- Review all files above.

- [ ] **Step 1: Re-read the approved spec and map every requirement to evidence**

Check modes `1/2/3/6/7`, error propagation, canonical schema, workflow handoff, package contents, and token handling.

- [ ] **Step 2: Run fresh final commands**

Run the focused plugin suite, workflow suite, archive inspection, YAML parse, and secret scan again. Only report success supported by these fresh results.

- [ ] **Step 3: Commit**

Not applicable: `E:\a-new\talor\dify\talordata-serp-main` is not a Git repository. Do not initialize a repository or create commits without user authorization.
