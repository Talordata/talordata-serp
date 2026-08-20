# 多格式 SERP 统一解析设计

## 背景与目标

Talordata SERP 的 `json` 参数默认值已经从 `2` 改为 `1`，调用方仍可显式覆盖。现有插件和 `TalorData SEO Visibility Agent.yaml` 主要依赖模式 `2` 的内嵌 JSON，导致模式 `1`、`3`、`6`、`7` 的真实返回无法稳定进入 SEO 可见度分析。

本次改造采用方案 A：在插件内完成多格式解析，向工作流输出统一的 `results` 记录；工作流优先消费统一记录，并保留对旧插件及历史响应的兼容回退。目标是让 `json=1/2/3/6/7` 都能经过同一套域名匹配、排名计算、证据链接和 AI 输入流程。

## 已验证的真实响应

真实请求使用 `engine=google`，并经过当前 `SerpClient` 的参数清理、表单编码和鉴权逻辑。

| 模式 | 已观察的成功形态 | 当前结果 |
| --- | --- | --- |
| `1` | `data.result.organic` 为对象数组；记录包含 `position`、`title`、`link`、`description` | 插件未下钻到 `data.result`，输出空 `results` |
| `2` | `data.result.json` 为 JSON 字符串，同时可含 `html`；解码后包含 `organic` | 工作流的历史回退可解析，插件仍输出空 `results` |
| `3` | `data.result` 为完整 Google HTML 字符串 | 当前无 HTML SERP 解析器 |
| `6` | 语义为 Markdown | 本轮真实请求只观察到字符串失败体，尚未取得成功 Markdown 样本 |
| `7` | 成功时为 `data.result.html` 与 `data.result.markdown` | 已真实取得成功体；也观察到字符串失败体 |

模式 `6/7` 还会出现 HTTP 和顶层业务码均正常，但 `data` 是 `error, Collection failed`、`md data retrieval failed` 或 `JSON fetch failed: ...` 的情况。这类响应必须判定为失败，不能作为“零结果搜索”继续分析。

## 统一输出契约

插件的 Web 搜索规范化结果保持现有顶层结构，并把每条自然搜索结果统一为：

```json
{
  "position": 1,
  "title": "Result title",
  "link": "https://example.com/page",
  "snippet": "Result description",
  "source": "example.com"
}
```

要求：

- `position` 为正整数。上游有明确排名时保留；没有时按有效自然结果的文档顺序生成。
- `title` 和 `link` 是有效结果的最低要求；缺少任一字段的候选项不进入 `results`。
- `snippet` 和 `source` 可为空字符串；`source` 缺失时可由 URL 主机名补齐。
- 链接统一解包 Google 跳转链接，排除 Google 自身导航、缓存、账户和搜索控制链接。
- 以规范化 URL 去重，保留首次出现且信息最完整的记录。
- `raw` 继续保留原始响应，便于诊断和向后兼容。
- 新增轻量解析元数据：`parse_format`、`parse_status`、`parse_error`。成功为 `parsed`，明确失败体为 `failed`，合法但无自然结果为 `empty`。

## 插件解析架构

### 响应解包

`unwrap_payload()` 扩展为识别 `data.result`，并分别暴露结构化对象、内嵌 JSON、HTML 和 Markdown。解包只负责发现载荷，不负责业务结果抽取。

载荷优先级：

1. 结构化 `organic_results`、`organic` 或 `results`。
2. `result.json` 解码后的结构化结果。
3. Markdown 结果。
4. HTML 结果。

模式 `7` 同时含 Markdown 和 HTML：两路都解析，然后按规范化 URL 合并。Markdown 顺序作为主顺序；HTML 用于补齐缺失标题、摘要或链接。若 Markdown 没有有效自然结果，则使用 HTML 结果。

### 结构化解析器（模式 1、2）

递归范围限制在已确认的容器键 `data`、`result`、`json`，结果列表键支持 `organic_results`、`organic`、`results`。避免在任意嵌套列表中误收集新闻、广告、购物或相关搜索。

字段映射：

- 排名：`position`、`rank`
- 标题：`title`、`name`
- 链接：`link`、`url`
- 摘要：`snippet`、`description`、`summary`
- 来源：`source`、`domain`

### HTML SERP 解析器（模式 3、7）

使用成熟 HTML DOM 解析库，不使用正则表达式解析标签。解析器围绕自然结果语义提取：候选项必须具有结果标题节点和可解析的外部链接，并从同一结果容器读取摘要。Google 的重定向链接先解包，再执行有效性和去重判断。

解析器不依赖单一易变 class 名；测试覆盖标准自然结果、Google `/url?q=` 跳转、重复链接、导航链接和缺少摘要等情况。

### Markdown SERP 解析器（模式 6、7）

使用 Markdown AST 解析库，不用逐行正则模拟 Markdown。解析器识别结果区段中的链接节点及其相邻文本，以文档顺序生成自然结果。元数据、AI URL、分页、相关搜索和 Google 内部链接不作为自然结果。

由于本轮 API 未返回成功的模式 6 载荷，模式 6 的自动化夹具使用模式 7 成功体中的 `markdown` 字段作为同格式契约；最终真实验收必须再次请求 `json=6`。若上游仍只返回明确失败体，验收记录为“错误识别正确、成功解析待上游恢复”，不能声称已验证成功内容。

### 失败识别

在内容解析前检查字符串载荷。匹配已真实观察到的错误前缀和短错误消息，包括 `error`、`failed`、`not found`。判定失败时：

- `results=[]`
- `parse_status="failed"`
- `parse_error` 保存有限长度的非敏感错误文本
- 工作流搜索状态为失败，不进入正常零结果结论

普通 HTML 或 Markdown 中出现单个 “failed” 单词不触发失败；失败识别只针对整个短字符串载荷或明确错误前缀。

## 工作流改造

目标文件为 `E:\a-new\talor\dify\TalorData SEO Visibility Agent.yaml`。

`Merge Search Result` 的输入策略调整为：

1. 优先读取新插件输出的统一 `results`。
2. 兼容读取 `organic_results`、`organic`。
3. 兼容旧模式 `2` 的 `raw.data.result.json`。
4. 兼容模式 `1` 的 `raw.data.result.organic`。
5. 若插件返回 `parse_status=failed`，传播失败原因，不把它压缩成成功空结果。

`Normalize SERP Evidence` 继续生成现有 `ai_input_json`，不改变 LLM 节点提示词和字段入口。统一结果中的 `position`、`title`、`link`、`snippet` 必须参与：

- 目标域名和竞品域名匹配
- 排名及 Top-N 可见度计算
- `evidence_links`
- `visibility_summary`
- `organic_parse_status`

插件版本从工作流当前固定的 `0.1.7` 更新到新包版本。Dify 插件依赖标识包含安装后生成的校验标识，不能手工猜测；安装新 `.difypkg` 后，在 Dify 编辑器中重新绑定工具节点，或使用 Dify 实际显示的完整依赖标识更新 YAML。

## 依赖与打包

在 `requirements.txt` 添加成熟的 HTML DOM 与 Markdown AST 解析依赖，并固定到与 Python 3.12、Dify 插件运行时兼容的版本范围。新增依赖必须包含在最终 `.difypkg` 的清单和安装解析中。

打包时更新 `talordata-serp.difypkg`，确认归档中的源码、依赖文件和 `manifest.yaml` 与工作目录一致。版本号按现有发布规则递增，避免用同一版本号覆盖行为不同的包。

## 测试与验收

### 自动化测试

- 模式 `1`：真实结构夹具可输出含排名的统一结果。
- 模式 `2`：内嵌 JSON 字符串可输出相同统一结果。
- 模式 `3`：Google HTML 夹具可提取自然结果、排名、链接和摘要。
- 模式 `6`：Markdown 夹具可提取自然结果并排除元数据链接。
- 模式 `7`：Markdown 与 HTML 合并、去重、补齐字段，顺序稳定。
- 失败体：已观察到的三类字符串被标记为 `failed`。
- 默认参数仍为 `json=1`，显式 `1/2/3/6/7` 均不被覆盖。
- 工作流代码节点测试确认统一 `results` 能到达并通过 `ai_input_json` JSON 解析。

### 真实 API 验收

对 `engine=google` 的 `json=1/2/3/6/7` 分别执行受控请求，并把每种响应送入实际插件规范化器和工作流的 Merge、Normalize 代码节点。验收记录至少包含：

- 原始载荷类型与关键字段，不保存 token。
- 插件 `parse_format`、`parse_status` 和结果数。
- 工作流自然结果数、证据链接数与解析状态。
- `ai_input_json` 可成功反序列化，且结果排名实际参与可见度计算。

模式 `6/7` 若返回明确上游失败体，应验证失败传播；只有取得成功内容并解析出有效自然结果，才记为该模式的成功内容验收通过。

## 安全与范围

- API token 只通过交互式标准输入使用，不写入源码、测试夹具、日志、YAML 或包文件。
- 测试夹具仅保存公开 SERP 的最小必要片段，不保存完整大响应。
- 不修改 LLM 提示词、SEO 评分公式或无关工具。
- 用户已在对话中公开过 token，完成测试后应轮换该 token。
