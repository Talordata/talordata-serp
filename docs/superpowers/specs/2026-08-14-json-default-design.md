# SERP JSON 默认值调整设计

## 目标

将所有 Talordata SERP 请求的 `json` 参数默认值从 `2` 调整为 `1`，同时保留调用方显式传入 `json` 时覆盖默认值的能力。

## 实现

- 修改 `utils/serp_client.py` 中 `_clean_params()` 的 `params.setdefault("json", 2)` 为 `params.setdefault("json", 1)`。
- 保持 `setdefault` 语义及 `isjson=1` 默认值不变。
- 不修改各搜索工具 YAML、请求格式、接口地址或响应处理。

## 验证

- 默认请求包含 `json=1&isjson=1`。
- 显式传入其他 `json` 值时，该值不被默认值覆盖。
- 完整测试套件通过。
- 更新后的 `.difypkg` 包含修改后的客户端代码，其他归档内容保持不变。
