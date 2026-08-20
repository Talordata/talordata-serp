# SERP JSON 默认值调整 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Talordata SERP 请求的 `json` 默认值从 `2` 调整为 `1`，并保留显式覆盖能力。

**Architecture:** 默认参数仍由 `SerpClient._clean_params()` 集中补充，继续使用 `dict.setdefault()`，所以所有搜索工具共享新默认值，而调用方提供的值优先。测试直接检查编码后的 HTTP 请求体，覆盖默认与显式覆盖两条路径。

**Tech Stack:** Python 3.12、pytest、Dify Plugin SDK

---

### Task 1: 锁定默认值和覆盖行为

**Files:**
- Modify: `tests/test_serp_client.py`
- Modify: `utils/serp_client.py:81`

- [ ] **Step 1: Write the failing test**

将现有默认请求断言中的 `json=2` 改为 `json=1`，并增加显式覆盖测试：

```python
def test_serp_client_preserves_explicit_json_value():
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeHttpResponse(200, '{"code":0,"data":{}}')

    client = SerpClient(endpoint=ENDPOINT, api_key="sk_test", urlopen=fake_urlopen)
    client.request({"engine": "google", "q": "coffee", "json": 7})

    request, _ = calls[0]
    assert request.data == b"engine=google&q=coffee&json=7&isjson=1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_serp_client.py`

Expected: 默认请求断言失败，实际请求仍包含 `json=2`；显式覆盖测试通过。

- [ ] **Step 3: Write minimal implementation**

在 `utils/serp_client.py` 中修改：

```python
params.setdefault("json", 1)
```

保持 `params.setdefault("isjson", 1)` 不变。

- [ ] **Step 4: Run tests to verify green**

Run: `pytest -q tests/test_serp_client.py`

Expected: `tests/test_serp_client.py` 全部通过。

Run: `pytest -q`

Expected: 完整测试套件全部通过。

### Task 2: 更新并检查 Dify 安装包

**Files:**
- Replace: `talordata-serp.difypkg`

- [ ] **Step 1: Update the packaged client**

复制现有安装包为临时 ZIP，使用 .NET ZIP API 按精确 entry 名替换客户端文件，再恢复 `.difypkg` 扩展名：

```powershell
Copy-Item -LiteralPath talordata-serp.difypkg -Destination talordata-serp.zip
$archive = [System.IO.Compression.ZipFile]::Open("talordata-serp.zip", "Update")
$archive.GetEntry("utils/serp_client.py").Delete()
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
    $archive,
    "utils/serp_client.py",
    "utils/serp_client.py"
)
$archive.Dispose()
Move-Item -LiteralPath talordata-serp.zip -Destination talordata-serp.difypkg -Force
```

- [ ] **Step 2: Inspect package contents**

确认包内 `utils/serp_client.py` 包含 `params.setdefault("json", 1)`，并确认归档中该路径仅出现一次。

- [ ] **Step 3: Run final verification**

Run: `pytest -q`

Expected: 完整测试套件全部通过。
