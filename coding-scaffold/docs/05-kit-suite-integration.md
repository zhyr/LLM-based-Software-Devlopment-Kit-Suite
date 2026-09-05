# 05 — Kit-Suite 其它脚本与 Coding Scaffold 集成分析

范围：仓库根目录遗留工具相对 `coding-scaffold`（Compose prompt+context）的取舍。

> **配套独立仓库（brew / 栖痕 / 疏引 / Al-exporter）与本仓的全局关系**不在本文展开，见仓库根目录 [`TOOLCHAIN.md`](../../TOOLCHAIN.md)。

## 结论一览

| 路径 | 状态 | 说明 |
|------|------|------|
| `clean-data.py` | **已模块化** | 策略在 `tools/llint/doc_noise.py`；Compose/`llint` 内存清洗。根脚本保留写盘离线用法 |
| `data-for-llm-crawl.py` + `crawler_config.json` | 保持独立 | ingest 旁路；勿塞进扩展核心 |
| `file_merger.py` / `project-structure-Explorer.py` | **保持现状** | 根目录与 `tools/legacy/` 并存；非整仓 dump 主路径 |
| `universal-reader-*.html` | 保持独立 | 浏览器宿主 |
| `js/vendor/` | 半成品 | Playground 用 CDN，不打进 vsix |
| `git-tidy.sh` / `disk_maintenance.sh` | 不进 vsix | 运维；`disk_maintenance.sh` 另被 [brew](https://github.com/zhyr/brew) 原样集成 |
| token / `findIncorrectLinks.js` | 归档级 | 与 compose 无关 |

## 与桌面配套仓的边界

| 能力 | 放哪 | 说明 |
|------|------|------|
| Compose / llint / Playground | 本仓 Scaffold | IDE 内主线 |
| 刘海启动器 / Agent 芯片 / 磁盘 UI | [眉梢 / brew](https://github.com/zhyr/brew) | 消费本仓清理脚本 + Al-exporter 约定 |
| Finder 取径、打开终端 | [疏引 / Vestige](https://github.com/zhyr/RightMenu) | 不进 vsix |
| 提示词记录树 | [栖痕 / Perch](https://github.com/zhyr/Perch) | 眉梢可唤起；Scaffold 不嵌入 |
| Agent 路径规范 | [Al-exporter](https://github.com/zhyr/Al-exporter) | 文档/约定仓，非 Scaffold 依赖 |

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
