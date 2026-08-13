# Enterprise — 企业私有仓配置

本目录存放 **可复制到企业私有仓** 的策略、schema 与 Agent 模板。

| 路径 | 说明 |
|------|------|
| `schemas/workspace-policy.schema.json` | 策略 JSON Schema（`privacy.mode: inject`） |
| `profiles/local-dev.example.yaml` | 本机开发默认策略 + KB 对齐内存流水线 |
| `templates/cursor-rules/` | 拷贝到目标仓 `.cursor/rules/`（源仓只读 + 动态注入） |
| `templates/AGENTS.md` | Agent 总则 |

**主线实现**：`tools/inject/resolve_context.py`（动态注入）。  
**扫描**：`tools/privacy/redact_workspace.py`（report-only，不改源）。  
见 [docs/04-privacy-kb-alignment.md](../docs/04-privacy-kb-alignment.md)。

用法见根目录 README 与 `tools/policy/`。
