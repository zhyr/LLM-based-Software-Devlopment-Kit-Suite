# 05 — Kit-Suite 其它脚本与 Coding Scaffold 集成分析

范围：仓库根目录遗留工具相对 `coding-scaffold`（Compose prompt+context）的取舍。

## 结论一览

| 路径 | 建议 | 理由 |
|------|------|------|
| `clean-data.py` | **宜模块化**进 `tools/llint` / 文档噪声步 | 清洗爬虫页脚噪声，可服务外链文档注入，默认仍不写源仓 |
| `data-for-llm-crawl.py` + `crawler_config.json` | **保持独立**（可选 sidecar） | ingest 旁路；勿塞进扩展核心 |
| `file_merger.py` / `project-structure-Explorer.py` | **归档** | 已与 `coding-scaffold/tools/legacy/` 重复；非整仓 dump 主路径 |
| `universal-reader-*.html` | **保持独立** | 浏览器宿主，与 IDE 扩展不同 |
| `js/vendor/`（showdown/mermaid/katex） | **半成品** | 无入口页；Playground 用 CDN 轻量页，不把 MB 级 vendor 打进 vsix |
| `git-tidy.sh` / `disk_maintenance.sh` | **永不进 vsix** | 运维脚本 |
| token 样例 / `findIncorrectLinks.js` | **归档级** | 与 compose 无关 |

README 中的 HaxiTAG-Assistant、Al-exporter、Yueli KGM 等为**外链能力**，不在本仓代码内。

## 推荐落地顺序

1. 根目录与 `tools/legacy` 去重说明（本文）  
2. 将 `clean-data` 策略抽为可选 compose 文档清洗步  
3. 爬虫配置化后再考虑「外链 → pack」旁路  
4. Playground：扩展命令打开本地页（见下），不把交互嵌进 Marketplace Details  

## Playground（Markdown / Mermaid）

**说明页（Details）只能渲染静态 README**，不能内嵌可编辑 playground。

可行做法（已采用）：

1. README 中给出 **Markdown / Mermaid** 两个入口说明  
2. 扩展命令打开 `playground/*.html`（本地预览 Compose 产出或手写草稿）  
3. 页面用 CDN 加载渲染库，避免 vsix 体积膨胀  

命令：

- `HaxiTAG: Open Markdown Playground`  
- `HaxiTAG: Open Mermaid Playground`  

源码：`coding-scaffold/playground/`。
