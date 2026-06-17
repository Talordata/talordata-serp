# Talordata SERP Marketplace Submission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare, verify, package, and submit the Talordata SERP Dify Tool Plugin to the official Dify Marketplace.

**Architecture:** The plugin source remains rooted at `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp`. Marketplace readiness work is split into documentation hardening, package verification, Dify runtime validation, and PR staging for `langgenius/dify-plugins`. Source behavior changes should be avoided unless a verification task exposes a real defect.

**Tech Stack:** Dify Plugin SDK for Python, Python 3.12 runtime, `pytest`, `requests`, Dify CLI `dify plugin package`, GitHub PR workflow.

---

## Assumptions and Decisions

- The Marketplace author remains `talordata` unless the actual GitHub owner used for the PR is different.
- The default Marketplace owner variable for this plan is `$MarketplaceOwner = "talordata"`.
- The current plugin version is `0.1.3`.
- The current source directory is `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp`.
- The generated package should be created from the parent directory with `dify plugin package talordata-serp`.
- Root `README.md` must stay English-only. Any Chinese documentation should live outside root README, for example `readme/README_zh_Hans.md`.
- `raw_serp_request` is the only public tool that should expose `params_json`.

---

## File Structure Map

- Modify: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\README.md`
  - Responsibility: English Marketplace-facing overview, credentials, tools, usage, limitations, support.
- Modify: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\PRIVACY.md`
  - Responsibility: data transmission, credential handling, logging/storage, Talordata policy links if available.
- Inspect only: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\manifest.yaml`
  - Responsibility: plugin metadata and Marketplace identity.
- Inspect only: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\provider\talordata_serp.yaml`
  - Responsibility: provider identity, credentials, and tool registry.
- Inspect only: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\tools\*.yaml`
  - Responsibility: Dify-visible tool parameters.
- Inspect only: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\.difyignore`
  - Responsibility: package exclusions.
- Create outside source checkout during PR staging: `C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace\talordata\talordata_serp\talordata_serp-0.1.3.difypkg`
  - Responsibility: Marketplace package file committed to the official plugin repository fork.

---

### Task 0: Prepare Source Repository and Package Exclusions

**Files:**
- Modify: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\.difyignore`
- Inspect: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\.git`

- [ ] **Step 1: Check whether the plugin source is a git repository**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
if (Test-Path -LiteralPath .git) {
  'source git repository: present'
} else {
  'source git repository: absent'
}
```

Expected: either result is acceptable. If absent, source commits in later tasks should be skipped or performed after the user initializes/publishes the plugin source repository.

- [ ] **Step 2: Ensure internal planning docs are excluded from `.difypkg`**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$ignore = Get-Content -Raw -Encoding UTF8 .difyignore
if ($ignore -notmatch '(?m)^docs/superpowers/$') {
  Add-Content -Encoding UTF8 .difyignore 'docs/superpowers/'
}
Select-String -Path .difyignore -Pattern '^docs/superpowers/$'
```

Expected:

```text
docs/superpowers/
```

- [ ] **Step 3: Commit `.difyignore` only when git is present**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
if (Test-Path -LiteralPath .git) {
  git add .difyignore
  git commit -m "chore: exclude planning docs from plugin package"
} else {
  'Skipping commit because plugin source is not a git repository'
}
```

Expected: commit succeeds when `.git` exists and `.difyignore` changed. If `.git` is absent, the skip message is expected.

---

### Task 1: Confirm Marketplace Identity

**Files:**
- Inspect: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\manifest.yaml`
- Inspect: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\provider\talordata_serp.yaml`
- No code changes unless the GitHub owner is not `talordata`.

- [ ] **Step 1: Read current identity fields**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
Select-String -Path manifest.yaml -Pattern '^author:|^name:|^version:|  version:|^verified:'
Select-String -Path provider\talordata_serp.yaml -Pattern 'author:|name:'
```

Expected:

```text
author: talordata
name: talordata_serp
version: 0.1.3
  version: 0.1.3
verified: false
```

- [ ] **Step 2: Decide the official Marketplace owner**

Use this rule:

```text
If the GitHub account or organization used for the Dify Marketplace PR is "talordata":
  keep manifest author as talordata.
If the GitHub account or organization is not "talordata":
  stop and ask whether to change manifest author or submit through a talordata-owned fork.
```

Expected: one explicit decision recorded in the PR notes:

```text
Marketplace owner: talordata
Manifest author: talordata
Official package directory: talordata/talordata_serp/talordata_serp-0.1.3.difypkg
```

- [ ] **Step 3: Verify no forbidden official identity is used**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$manifestAuthor = (Select-String -Path manifest.yaml -Pattern '^author:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
$manifestName = (Select-String -Path manifest.yaml -Pattern '^name:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
$providerAuthor = (Select-String -Path provider\talordata_serp.yaml -Pattern '^\s*author:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
$providerName = (Select-String -Path provider\talordata_serp.yaml -Pattern '^\s*name:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
$values = @($manifestAuthor, $manifestName, $providerAuthor, $providerName)
if ($values -contains 'langgenius' -or $values -contains 'dify') {
  "Reserved identity found: $($values -join ', ')"
  exit 1
}
"Identity fields are not using reserved official names: $($values -join ', ')"
```

Expected:

```text
Identity fields are not using reserved official names: talordata, talordata_serp, talordata, talordata_serp
```

- [ ] **Step 4: Commit only if identity changes were made**

If no file changed, do not commit. If author/name/version was changed after user approval:

```powershell
if (Test-Path -LiteralPath .git) {
  git add manifest.yaml provider\talordata_serp.yaml
  git commit -m "chore: align marketplace plugin identity"
} else {
  'Skipping commit because plugin source is not a git repository'
}
```

Expected: commit succeeds only when identity files actually changed and `.git` exists. If `.git` is absent, the skip message is expected.

---

### Task 2: Harden README for Marketplace Review

**Files:**
- Modify: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\README.md`

- [ ] **Step 1: Write a failing README requirements check**

Run this PowerShell check before editing:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$readme = Get-Content -Raw -Encoding UTF8 README.md
$required = @(
  '## Credentials',
  '## Actions',
  '## Usage',
  '## Limitations',
  '## Support'
)
$missing = $required | Where-Object { $readme -notmatch [regex]::Escape($_) }
if ($missing) {
  "MISSING: $($missing -join ', ')"
  exit 1
}
if ($readme -match '[\u4e00-\u9fff]') {
  'README contains Chinese characters'
  exit 1
}
'README marketplace sections present'
```

Expected before this task: FAIL because `## Usage`, `## Limitations`, or `## Support` may be missing.

- [ ] **Step 2: Add or update `## Usage` in README**

Insert this section after the existing actions/raw request description and before `## Development`:

````markdown
## Usage

1. Install the plugin package in Dify.
2. Configure the provider credentials with a Talordata SERP API key.
3. Add a search tool, such as Bing Search or Google Search, to a workflow or agent.
4. Map the user query to the tool's query field, for example `q`.
5. Run the workflow and consume the returned structured JSON results.

Example Bing Search input:

```json
{
  "q": "latest AI search trends",
  "cc": "us",
  "mkt": "en-us",
  "count": 10
}
```

Use `raw_serp_request` when advanced engine-specific parameters are required:

```json
{
  "engine": "google",
  "q": "coffee",
  "params_json": "{\"gl\":\"us\",\"hl\":\"en\",\"num\":10}"
}
```
````

Check indentation carefully: nested fenced JSON blocks inside Markdown must be valid.

- [ ] **Step 3: Add or update `## Limitations` in README**

Add this exact section after `## Usage`:

```markdown
## Limitations

- Search availability, freshness, latency, quota, and rate limits depend on the Talordata SERP API and the user's Talordata account plan.
- Some vertical engines return complex upstream payloads. The plugin wraps those responses in a stable JSON object instead of flattening every field.
- The plugin does not store Talordata dashboard login JWT tokens and does not require them for SERP requests.
- Avoid placing unnecessary sensitive personal data in search queries.
```

- [ ] **Step 4: Add or update `## Support` in README**

Add this section after `## Limitations`:

```markdown
## Support

For issues with the Dify plugin package, report a GitHub issue in the repository used for this plugin submission.

For Talordata SERP API account, quota, or API key issues, contact Talordata support through the official Talordata support channel.
```

If a real support URL or email is available, replace the generic wording with the real support endpoint.

- [ ] **Step 5: Run the README check again**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$readme = Get-Content -Raw -Encoding UTF8 README.md
$required = @(
  '## Credentials',
  '## Actions',
  '## Usage',
  '## Limitations',
  '## Support'
)
$missing = $required | Where-Object { $readme -notmatch [regex]::Escape($_) }
if ($missing) {
  "MISSING: $($missing -join ', ')"
  exit 1
}
if ($readme -match '[\u4e00-\u9fff]') {
  'README contains Chinese characters'
  exit 1
}
'README marketplace sections present'
```

Expected: PASS with `README marketplace sections present`.

- [ ] **Step 6: Commit README hardening**

Run:

```powershell
if (Test-Path -LiteralPath .git) {
  git add README.md
  git commit -m "docs: strengthen marketplace readme"
} else {
  'Skipping commit because plugin source is not a git repository'
}
```

Expected: commit succeeds when `.git` exists. If `.git` is absent, the skip message is expected and the file changes remain in the working directory for later source publication.

---

### Task 3: Harden Privacy Disclosure

**Files:**
- Modify: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\PRIVACY.md`

- [ ] **Step 1: Write a failing privacy requirements check**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$privacy = Get-Content -Raw -Encoding UTF8 PRIVACY.md
$required = @(
  'Talordata SERP API',
  'SERP API Key',
  'search query',
  'engine',
  'country',
  'language',
  'The plugin does not store'
)
$missing = $required | Where-Object { $privacy -notmatch [regex]::Escape($_) }
if ($missing) {
  "MISSING: $($missing -join ', ')"
  exit 1
}
'PRIVACY baseline disclosure present'
```

Expected before editing: PASS or PARTIAL. If it passes, still continue with Step 2 to make the disclosure review-ready.

- [ ] **Step 2: Replace `PRIVACY.md` with review-ready content**

Use this content:

```markdown
# Privacy

This plugin sends the search parameters entered or configured in Dify to the Talordata SERP API in order to return search results.

Data that may be sent to Talordata SERP API includes:

- search query
- selected SERP engine
- country, region, market, and language parameters
- location, latitude, and longitude parameters when configured
- pagination and result count parameters
- image, video, shopping, maps, news, scholar, finance, patent, hotel, flight, and other engine-specific filters
- advanced parameters provided through `raw_serp_request`

The plugin uses the SERP API Key configured by the Dify workspace user. The key is used only to authenticate requests to the Talordata SERP API.

The plugin does not require or store Talordata dashboard login JWT tokens. The plugin does not intentionally persist search queries, API responses, or API keys outside of Dify's normal plugin runtime and credential storage.

Users should avoid submitting unnecessary sensitive personal data in search queries or request parameters.

Talordata SERP API processing, retention, quota, and rate-limit behavior are governed by Talordata's service terms and privacy policy.
```

If a real Talordata privacy policy URL is available before submission, append this exact sentence with the real URL:

```markdown

Talordata privacy policy: https://example.com/privacy
```

- [ ] **Step 3: Run the privacy check again**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$privacy = Get-Content -Raw -Encoding UTF8 PRIVACY.md
$required = @(
  'Talordata SERP API',
  'SERP API Key',
  'search query',
  'selected SERP engine',
  'country, region, market, and language',
  'The plugin does not require or store Talordata dashboard login JWT tokens',
  'Users should avoid submitting unnecessary sensitive personal data'
)
$missing = $required | Where-Object { $privacy -notmatch [regex]::Escape($_) }
if ($missing) {
  "MISSING: $($missing -join ', ')"
  exit 1
}
'PRIVACY marketplace disclosure present'
```

Expected: PASS with `PRIVACY marketplace disclosure present`.

- [ ] **Step 4: Commit privacy hardening**

Run:

```powershell
if (Test-Path -LiteralPath .git) {
  git add PRIVACY.md
  git commit -m "docs: clarify privacy disclosure"
} else {
  'Skipping commit because plugin source is not a git repository'
}
```

Expected: commit succeeds when `.git` exists. If `.git` is absent, the skip message is expected.

---

### Task 4: Verify Tool Parameter Surface

**Files:**
- Inspect: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\tools\*.yaml`
- Inspect: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp\tests\test_generate_serp_tools.py`

- [ ] **Step 1: Run the targeted regression test**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
.\.venv\Scripts\python.exe -m pytest tests/test_generate_serp_tools.py -q
```

Expected:

```text
5 passed
```

Warnings from Dify SDK or gevent may appear; they are acceptable if pytest exits with code 0.

- [ ] **Step 2: Verify only raw request exposes `params_json`**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
Get-ChildItem -LiteralPath .\tools -Filter '*.yaml' | ForEach-Object {
  $text = Get-Content -Raw -LiteralPath $_.FullName
  if ($text -match 'name:\s*params_json') { $_.Name }
}
```

Expected:

```text
raw_serp_request.yaml
```

- [ ] **Step 3: Stop on unexpected output**

If any file other than `raw_serp_request.yaml` appears, do not continue to package. Regenerate tools and rerun tests:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
.\.venv\Scripts\python.exe scripts\generate_serp_tools.py
.\.venv\Scripts\python.exe -m pytest tests/test_generate_serp_tools.py -q
```

Expected after regeneration: `5 passed`, and only `raw_serp_request.yaml` exposes `params_json`.

---

### Task 5: Full Local Verification

**Files:**
- Inspect all plugin files.
- No edits unless tests reveal a defect.

- [ ] **Step 1: Run full unit test suite**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
.\.venv\Scripts\python.exe -m pytest -q
```

Expected:

```text
43 passed
```

Warnings from Dify SDK, gevent, or pydantic are acceptable if the exit code is 0.

- [ ] **Step 2: Validate README remains English-only**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
$readme = [System.IO.File]::ReadAllText((Resolve-Path README.md), [System.Text.Encoding]::UTF8)
if ($readme -match '[\u4e00-\u9fff]') {
  'README contains Chinese characters'
  exit 1
}
'README English-only check: PASS'
```

Expected:

```text
README English-only check: PASS
```

- [ ] **Step 3: Validate package exclusions**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
Get-Content .difyignore
```

Expected includes:

```text
__pycache__/
*.py[cod]
.pytest_cache/
.env
.venv/
tests/
docs/superpowers/
*.difypkg
.git/
.gitignore
```

- [ ] **Step 4: Commit verification-related doc changes**

If Tasks 2 or 3 changed docs and no commit was made:

```powershell
if (Test-Path -LiteralPath .git) {
  git add README.md PRIVACY.md .difyignore
  git commit -m "docs: prepare marketplace submission"
} else {
  'Skipping commit because plugin source is not a git repository'
}
```

Expected: commit succeeds when `.git` exists, or no commit is needed because the files were already committed. If `.git` is absent, the skip message is expected.

---

### Task 6: Repackage Plugin

**Files:**
- Output: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp.difypkg`

- [ ] **Step 1: Remove stale local package if needed**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins
if (Test-Path .\talordata-serp.difypkg) {
  Remove-Item .\talordata-serp.difypkg
}
```

Expected: no error. This removes only the parent-directory package artifact, not source.

- [ ] **Step 2: Package from parent directory**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins
dify plugin package talordata-serp
```

Expected:

```text
plugin packaged successfully output_path=talordata-serp.difypkg
```

- [ ] **Step 3: Verify package exists and is small**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins
Get-Item .\talordata-serp.difypkg | Select-Object FullName,Length,LastWriteTime
```

Expected:

```text
FullName ... C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp.difypkg
Length   ... under 1 MB
```

If package size is tens of MB, inspect `.difyignore` and ensure `.venv`, tests, caches, and local package artifacts are excluded.

---

### Task 7: Install and Test in Dify

**Files:**
- Input package: `C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp.difypkg`
- No source changes unless Dify verification exposes a real defect.

- [ ] **Step 1: Upload latest package to Dify**

In Dify UI:

```text
Plugins -> Install from local package -> select C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp.difypkg
```

Expected: plugin installs or updates to version `0.1.3`.

- [ ] **Step 2: Configure provider credentials**

In Dify UI:

```text
Provider: Talordata SERP
SERP Endpoint: keep default unless production endpoint is required
SERP API Key: use a valid Talordata SERP API key beginning with sk_
```

Expected: credential save succeeds. If validation fails, capture the exact error message and inspect endpoint/key pairing.

- [ ] **Step 3: Re-add a common search node**

Create a new workflow test:

```text
Start/User Input -> Bing Search -> End
```

Expected Bing Search visible parameters include `q`, `device`, `location`, `cc`, `mkt`, `first`, `count`, and related typed fields. Expected absent parameter: `params_json`.

- [ ] **Step 4: Run Bing Search**

Use this input:

```json
{
  "q": "coffee",
  "cc": "us",
  "mkt": "en-us",
  "count": 3
}
```

Expected: tool succeeds and returns structured JSON with query/engine/results or raw wrapper depending on upstream response.

- [ ] **Step 5: Run Google Search**

Use this input:

```json
{
  "q": "coffee",
  "gl": "us",
  "hl": "en",
  "num": 3
}
```

Expected: tool succeeds and returns structured JSON. If the visible field is `count` instead of `num` for a specific Google tool, use the exact field exposed by that tool YAML.

- [ ] **Step 6: Run Raw SERP Request**

Use this input:

```json
{
  "engine": "google",
  "q": "coffee",
  "params_json": "{\"gl\":\"us\",\"hl\":\"en\",\"num\":3}"
}
```

Expected: tool succeeds. `params_json` should be visible here because this is the advanced raw tool.

- [ ] **Step 7: Record manual verification evidence**

Record this evidence for PR:

```text
Dify install: PASS
Provider credential validation: PASS
Bing Search: PASS
Google Search: PASS
Raw SERP Request: PASS
Common tool params_json hidden: PASS
```

If any item fails, record:

```text
Tool:
Input:
Error:
Screenshot or log:
Hypothesis:
Next step:
```

Do not submit Marketplace PR until the failure is understood or documented as an external credential/quota issue.

---

### Task 8: Stage Official Marketplace Repository PR

**Files:**
- Create in official fork checkout: `<official-dify-plugins-fork>\talordata\talordata_serp\talordata_serp-0.1.3.difypkg`

- [ ] **Step 1: Clone or open the fork of official plugin repository**

If not cloned:

```powershell
cd C:\Users\Administrator\Desktop\tolar
$MarketplaceOwner = "talordata"
git clone "https://github.com/$MarketplaceOwner/dify-plugins.git" dify-plugins-marketplace
cd dify-plugins-marketplace
git remote add upstream https://github.com/langgenius/dify-plugins.git
git fetch upstream
git checkout -b add-talordata-serp-0.1.3 upstream/main
```

Expected: branch `add-talordata-serp-0.1.3` exists.

If already cloned, use:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace
$MarketplaceOwner = "talordata"
git fetch upstream
git checkout -b add-talordata-serp-0.1.3 upstream/main
```

- [ ] **Step 2: Create package directory**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace
New-Item -ItemType Directory -Force -Path .\talordata\talordata_serp | Out-Null
```

Expected: directory exists.

- [ ] **Step 3: Copy package with official filename**

Run:

```powershell
Copy-Item `
  -LiteralPath C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp.difypkg `
  -Destination C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace\talordata\talordata_serp\talordata_serp-0.1.3.difypkg `
  -Force
```

Expected: destination file exists.

- [ ] **Step 4: Verify official repo diff**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace
git status --short
```

Expected:

```text
?? talordata/talordata_serp/talordata_serp-0.1.3.difypkg
```

- [ ] **Step 5: Commit package**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace
git add talordata/talordata_serp/talordata_serp-0.1.3.difypkg
git commit -m "add talordata serp plugin"
```

Expected: commit succeeds.

- [ ] **Step 6: Push branch**

Run:

```powershell
git push origin add-talordata-serp-0.1.3
```

Expected: branch pushed to fork.

---

### Task 9: Create English Pull Request

**Files:**
- No local source changes.
- PR body in GitHub UI.

- [ ] **Step 1: Decide the support contact for the PR body**

Use this rule:

```text
If a public GitHub Issues URL exists for the plugin source repository:
  Support contact = that GitHub Issues URL.
If no public issue tracker exists but a support email is approved:
  Support contact = the approved support email.
If neither exists:
  stop before opening the PR and ask the user for the support contact.
```

Expected example:

```text
Support contact: https://github.com/talordata/talordata-serp-dify-plugin/issues
```

- [ ] **Step 2: Use this PR title**

```text
Add Talordata SERP plugin
```

- [ ] **Step 3: Use this PR body after replacing the support contact line**

Before pasting the PR body, replace `SUPPORT_CONTACT` with the real support contact decided in Step 1. Do not submit the PR while `SUPPORT_CONTACT` remains in the body.

````markdown
## Overview

This PR adds the Talordata SERP plugin for Dify. It provides real-time structured SERP tools for workflows and agents.

## Tools

- Bing Search, Images, Maps, News, Shopping, Videos
- Google Search, Web, Images, News, Shopping, Maps, Local, Videos, Jobs, Flights, Hotels, Trends
- Google Scholar, Patents, Finance, Play
- DuckDuckGo Search
- Yandex Search
- Raw SERP Request for advanced parameters

## Credentials

This plugin requires a Talordata SERP API key configured as a provider credential.

## Notes

Common search tools expose standard parameters directly. Advanced JSON parameters are available through `raw_serp_request`.

## Tests

- Installed dependencies with `pip install -r requirements.txt`
- Ran `python -m pytest -q` (`43 passed`)
- Packaged with `dify plugin package talordata-serp`
- Installed the generated `.difypkg` in Dify
- Tested Bing Search with a valid Talordata SERP API key
- Tested Google Search with a valid Talordata SERP API key
- Verified common search tools no longer expose `params_json`

## Support

Issues can be reported at: SUPPORT_CONTACT
````

- [ ] **Step 4: Submit PR to official repository**

Before submitting, verify the PR body no longer contains:

```text
SUPPORT_CONTACT
```

Expected: no `SUPPORT_CONTACT` text remains in the PR body.

Target:

```text
base repo: langgenius/dify-plugins
base branch: main
compare branch: talordata:add-talordata-serp-0.1.3
```

Expected: PR created successfully.

- [ ] **Step 5: Save PR URL**

After GitHub creates the PR, copy the actual browser URL and record it in the Marketplace checklist. The recorded value must look like this shape, with a real numeric PR id:

```text
Marketplace PR: https://github.com/langgenius/dify-plugins/pull/12345
```

---

### Task 10: Post-Submission Tracking

**Files:**
- Optional modify: `C:\Users\Administrator\Desktop\SerpAPI Dify 插件官方 Marketplace 提交清单（2026-06-12 核验版）.md`

- [ ] **Step 1: Monitor CI and reviewer comments**

Check PR page after submission.

Expected:

```text
No CI failure caused by package path, filename, or package validation.
```

- [ ] **Step 2: If reviewer asks for changes, classify the request**

Use this classification:

```text
Docs-only:
  update README.md or PRIVACY.md, repackage, update difypkg, push PR.
Metadata:
  update manifest.yaml/provider identity, repackage, update difypkg, push PR.
Runtime bug:
  write failing test in plugin source, fix code, run full tests, repackage, update difypkg, push PR.
Marketplace path issue:
  move difypkg to requested official path, amend commit or add new commit.
```

- [ ] **Step 3: Repackage after any source change**

Run:

```powershell
cd C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp
.\.venv\Scripts\python.exe -m pytest -q

cd C:\Users\Administrator\Desktop\tolar\dify-plugins
dify plugin package talordata-serp
```

Expected: tests pass and package succeeds.

- [ ] **Step 4: Update official PR package**

Run:

```powershell
Copy-Item `
  -LiteralPath C:\Users\Administrator\Desktop\tolar\dify-plugins\talordata-serp.difypkg `
  -Destination C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace\talordata\talordata_serp\talordata_serp-0.1.3.difypkg `
  -Force

cd C:\Users\Administrator\Desktop\tolar\dify-plugins-marketplace
git add talordata/talordata_serp/talordata_serp-0.1.3.difypkg
git commit -m "update talordata serp plugin package"
git push origin add-talordata-serp-0.1.3
```

Expected: PR updates automatically.

---

## Self-Review

Spec coverage:

- Official submission method: Tasks 1, 8, 9.
- Author / owner consistency: Task 1.
- README Marketplace readiness: Task 2.
- Privacy disclosure: Task 3.
- Hidden `params_json` regression: Task 4.
- Full tests and package verification: Tasks 5 and 6.
- Dify installation and real API testing: Task 7.
- PR body and support contact: Task 9.
- Reviewer response workflow: Task 10.

Known gaps that require user or external input:

- Real GitHub owner or organization for Marketplace submission.
- Real Talordata support URL or email.
- Real Talordata privacy policy URL.
- Valid Talordata SERP API key for Dify runtime verification.
- Existing local path of the user's fork of `langgenius/dify-plugins`, if already cloned.

No source behavior changes are planned unless verification exposes a defect. The plan favors documentation hardening, repeatable verification, and packaging discipline.
