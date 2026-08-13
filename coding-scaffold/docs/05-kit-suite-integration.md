# 05 — Kit-Suite 其它脚本与 Coding Scaffold 集成分析

范围：仓库根目录遗留工具相对 `coding-scaffold`（Compose prompt+context）的取舍。

## 结论一览

| 路径 | 状态 | 说明 |
|------|------|------|
| `clean-data.py` | **已模块化** | 策略在 `tools/llint/doc_noise.py`；Compose/`llint` 内存清洗。根脚本保留写盘离线用法 |
| `data-for-llm-crawl.py` + `crawler_config.json` | 保持独立 | ingest 旁路；勿塞进扩展核心 |
| `file_merger.py` / `project-structure-Explorer.py` | **保持现状** | 根目录与 `tools/legacy/` 并存；非整仓 dump 主路径 |
| `universal-reader-*.html` | 保持独立 | 浏览器宿主 |
| `js/vendor/` | 半成品 | Playground 用 CDN，不打进 vsix |
| `git-tidy.sh` / `disk_maintenance.sh` | 不进 vsix | 运维 |
| token / `findIncorrectLinks.js` | 归档级 | 与 compose 无关 |

## 文档噪声（clean-data → llint）

Compose 在 `llint` 步默认启用 `docNoise`：

- 去掉 `(共N页, 全文M字)`、`(本页字数: …, URL: …)` 等爬虫脚注  
- 策略可被 `ime.docNoiseStrategies` 覆盖；`--no-doc-noise` 关闭  
- **不写源仓**（与根目录 `clean-data.py` 写 `*_cleaned.txt` 不同）

## Playground

Details 页只能静态 README。命令：

- `HaxiTAG: Open Markdown Playground`  
- `HaxiTAG: Open Mermaid Playground`  

源码：`coding-scaffold/playground/`。
