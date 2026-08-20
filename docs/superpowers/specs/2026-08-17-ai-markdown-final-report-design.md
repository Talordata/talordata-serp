# AI Markdown Final Report Design

## Context

The workflow successfully sends normalized SERP evidence to its LLM node, but the current `Validate and Build Result` entry point ignores the `analysis` argument and always renders a deterministic report from `report`. The YAML also contains an existing strict Markdown validator whose expected report contract no longer matches the current LLM prompt.

## Goal

Use a well-formatted, evidence-constrained AI Markdown brief as the final report when it passes the workflow's existing safety checks. Fall back to deterministic Markdown when the model output is malformed, unsafe, unsupported, or inconsistent with normalized SERP evidence.

The default LLM provider and model remain unchanged. Users may replace `gpt-4o` in Dify, and the regression test will use the supplied DeepSeek connection only as an external compatibility test.

## Report Contract

The LLM must return Markdown only, beginning immediately with:

```markdown
# SEO Visibility Industry Brief
```

It must include each section exactly once and in this order:

1. `## Executive Summary`
2. `## Keyword Visibility`
3. `## Competitor Landscape`
4. `## Priority Opportunities`
5. `## Recommended Actions`
6. `## Data Quality and Limitations`

Keyword visibility must use this exact table header:

```markdown
| Keyword | TalorData Performance | Page / Evidence | Priority | Recommended Action |
```

Competitor visibility must use this exact table header:

```markdown
| Keyword | Competitor | Competitor Performance | Ahead of Target Site? | Competitor Page / Evidence |
```

When no competitor evidence exists, the model must output exactly this single data row:

```markdown
| None | No competitor evidence | Insufficient data to determine ranking. | Not verified | None |
```

The prompt will prohibit preambles, HTML, code fences, visible reasoning, `<think>` tags, invented keywords, invented rankings, and URLs outside `allowed_evidence_links`. It will require `Insufficient data to determine ranking.` whenever normalized evidence does not permit a ranking conclusion.

## Data Flow

```text
Normalize SERP Evidence
  -> ai_input_json
  -> LLM Markdown analysis
  -> validate_markdown_analysis
       -> valid: use sanitized AI Markdown
       -> invalid: deterministic_markdown fallback
  -> Markdown JSON envelope
  -> webhook payload / final workflow result
```

`Validate and Build Result.main()` will:

1. Validate and canonicalize `allowed_evidence_links`.
2. Pass `analysis`, deterministic `report`, allowed keywords, and allowed links to the existing `validate_markdown_analysis()` helper.
3. Use the validated AI Markdown when accepted.
4. Mark the result `partial` when a single outer Markdown fence or one leading closed reasoning block had to be removed.
5. Use `deterministic_markdown()` and mark the result `partial` when validation fails.
6. Preserve an upstream `failed` report status.
7. Keep the existing 200 KB output limit and JSON envelope:

```json
{
  "status": "completed | partial | failed",
  "report_format": "markdown",
  "report_markdown": "..."
}
```

## Safety Rules

The existing validator remains authoritative for:

- exact title, required sections, and section order;
- exact keyword and competitor table schemas;
- keyword membership in `allowed_keywords`;
- ranking claims matching normalized evidence;
- competitor claims matching normalized evidence;
- links restricted to exact values in `allowed_evidence_links`;
- rejection of HTML, nested code fences, control characters, hidden URLs, encoded unsafe URLs, and oversized output;
- removal of at most one complete leading `<think>...</think>` block or one outer Markdown fence, with a `partial` status.

## Testing

Automated tests will first demonstrate the current failure: two distinct valid AI briefs must produce distinct final reports, while the current entry point produces the same deterministic output.

Regression coverage will verify:

- the prompt and validator share the exact Markdown contract;
- a valid AI brief becomes the final `report_markdown`;
- different valid AI briefs produce different final reports;
- one outer fence or one leading closed reasoning block is removed and marked `partial`;
- malformed sections, invented keywords, invented rankings, HTML, unsafe URLs, and unknown evidence links use the deterministic fallback;
- payload serialization and final result wrapping preserve the selected report;
- existing workflow-focused tests pass.

After automated verification, real end-to-end tests will run `json=1,2,3,6,7` through the final `.difypkg`, workflow Merge/Normalize code, the supplied DeepSeek test model using the workflow prompt, validated AI Markdown, and final result serialization. TalorData and DeepSeek credentials must remain only in their existing source or hidden terminal input and must not be copied into scripts, logs, reports, or packages.

## Non-Goals

- Changing the workflow's default `gpt-4o` model configuration.
- Sending a real webhook during testing.
- Relaxing evidence, ranking, URL, or output-size safeguards.
- Changing the TalorData plugin package unless testing identifies a separate plugin defect.
