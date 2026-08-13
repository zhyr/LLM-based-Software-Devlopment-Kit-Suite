# LLM-based-Software-Devlopment-Kit-Suite

LLM 辅助软件开发工具集合（HaxiTAG）。

**当前推荐入口：[coding-scaffold](coding-scaffold/) — HaxiTAG Coding Scaffold**  
私有仓库 × AI Coding IDE（VS Code / Cursor / CodeBuddy）对接扩展：在进入对话前整理 **prompt + context**，可配合 [Forge](https://haxitag.com/community/forge) / Sentinel。

---

## HaxiTAG Coding Scaffold（主线）

| 项 | 说明 |
|----|------|
| 定位 | 私有仓与 AI Coding 的对接插件（非编码 Agent 本体） |
| 主能力 | Compose Input：隐私清洗 → llint → 命名对齐 → 线性编排 → prompt；可选 Sentinel |
| 安装包 | [`coding-scaffold/dist/haxitag-coding-scaffold-0.5.2.vsix`](coding-scaffold/dist/haxitag-coding-scaffold-0.5.2.vsix)（版本以 `extension/package.json` 为准） |
| 说明 | [`coding-scaffold/README.md`](coding-scaffold/README.md) · 扩展详情 [`extension/README.md`](coding-scaffold/extension/README.md) |
| 官网 | [https://haxitag.com/community/forge](https://haxitag.com/community/forge) |

### 快速启用（Cursor）

```bash
# 1) 安装扩展
cursor --install-extension coding-scaffold/dist/haxitag-coding-scaffold-0.5.2.vsix

# 2) 写入策略模板到私有仓
cd coding-scaffold
python3 tools/policy/bootstrap_workspace.py --root /path/to/private-repo --profile local-dev

# 3) 用 Cursor 打开该私有仓 → 命令面板运行
#    HaxiTAG: Compose Input (prompt + context) → 粘贴进 Chat/Agent
```

也可：Extensions → **Install from VSIX…**。校验/扫描见 `coding-scaffold/README.md`。

### 从本仓打包扩展

```bash
cd coding-scaffold/extension && npm install && npm run package:vsix
# 产物：../dist/haxitag-coding-scaffold-<version>.vsix
```

### 与 Kit-Suite 其它工具的关系

根目录仍有爬虫清洗、书签阅读器、磁盘清理等**遗留脚本**。哪些适合并入 Scaffold、哪些保持独立，见：

→ **[`coding-scaffold/docs/05-kit-suite-integration.md`](coding-scaffold/docs/05-kit-suite-integration.md)**

结论摘要：`clean-data` 类文档噪声清洗适合并入 compose 流水线；爬虫 / 书签阅读器 / 磁盘与 git 清理保持独立；根目录 `file_merger` / `structure-Explorer` 已与 `coding-scaffold/tools/legacy/` 重复。

---

## 仓库根目录其它工具（遗留）

| 工具 | 用途 | 与 Scaffold |
|------|------|-------------|
| `data-for-llm-crawl.py` + `crawler_config.json` | 文档站爬取 → markdown | 可选旁路 ingest，不进扩展核心 |
| `clean-data.py` | 清洗爬虫产物噪声 | **建议**模块化进 llint/文档清洗 |
| `file_merger.py` / `project-structure-Explorer.py` | 合并全文 / 目录树 | 已迁 legacy，勿再当主路径 |
| `universal-reader-*.html` | 网页 → markdown（浏览器） | 保持独立 |
| `js/vendor/` | showdown / mermaid / katex 等 | 半成品预览栈；Playground 见 Scaffold |
| `git-tidy.sh` / `disk_maintenance.sh` | 仓库 gc / 开发机清理 | 运维，不进 vsix |
| token / `findIncorrectLinks.js` | 样例或历史 lint | 归档级 |

外链相关能力：[HaxiTAG-Assistant](https://github.com/zhyr/HaxiTAG-Assistant)、[Al-exporter](https://github.com/zhyr/Al-exporter) 等不在本仓代码内。

---

## Playground（Markdown / Mermaid）

扩展 **Details 页是静态 README**，无法在说明页内嵌交互预览。  
已在 Coding Scaffold 提供本地 Playground，并通过扩展命令打开：

- `HaxiTAG: Open Markdown Playground`
- `HaxiTAG: Open Mermaid Playground`

页面源码：[`coding-scaffold/playground/`](coding-scaffold/playground/)。说明见集成文档与扩展 README。

---

## License / 维护

源码目录以 `coding-scaffold/` 为主迭代；根目录遗留脚本按上表逐步归档或模块化，避免与 Compose 主线混淆。
