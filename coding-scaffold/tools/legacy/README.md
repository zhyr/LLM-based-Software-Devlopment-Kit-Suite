# Legacy tools (2024)

这些脚本从 HaxiTAG-AI-CMS / 早期 Kit-Suite 抽离，**默认不再作为企业私有仓主线**。

| 脚本 | 状态 | 说明 |
|------|------|------|
| `haxitag-path-annotator.py` | 不推荐 | 污染 diff；Agent 已有路径感知 |
| `haxitag-structure-Explorer.py` | 诊断可用 | 导出目录树 |
| `AICMS-structure-Explorer.py` | 诊断可用 | 变体 |
| `project-structure-Explorer.py` | 诊断可用 | 更早版本 |
| `haxitag-context-builder.py` | 受限可用 | 全文合并；应用 policy 过滤后再考虑 |
| `file_merger.py` | 受限可用 | 同上 |
| `HaxiTAG-multi-language.py` | 可用 | i18n 抽取，与 Agent 上下文无关 |

新能力请放到 `tools/policy/` 或未来的 `tools/context/`，不要继续扩展本目录。
