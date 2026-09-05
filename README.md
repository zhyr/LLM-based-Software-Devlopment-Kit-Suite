# LLM-based-Software-Devlopment-Kit-Suite

LLM 辅助软件开发工具集合（HaxiTAG）。

本仓是工具链的**枢纽仓库**：以 **Coding Scaffold** 为主线（IDE 内 Compose），根目录保留运维与遗留脚本；桌面侧配套应用（刘海屏、Finder、剪贴板记录等）在独立仓库维护。

**完整关系视图（必读）：[`TOOLCHAIN.md`](TOOLCHAIN.md)**  
**当前推荐入口：[coding-scaffold](coding-scaffold/) — HaxiTAG Coding Scaffold**  
私有仓库 × AI Coding IDE（VS Code / Cursor / CodeBuddy）对接扩展：在进入对话前整理 **prompt + context**，可配合 [Forge](https://haxitag.com/community/forge) / Sentinel。

---

## 工具链一览

**命名约定**：眉梢 = brew.app · 栖痕 = Perch · 疏引 = Vestige

```text
Kit Suite（本仓）── Compose / 运维脚本
        │
        ├── 眉梢 brew.app ──刘海中枢──► 栖痕 Perch（记录回喂）
        │         ▲
        │         └── Al-exporter（Agent 路径约定）
        │
        └── 疏引 Vestige ──Finder 取径──► 粘贴进对话 / 栖痕 / 终端
```

| 角色 | 产品 | 仓库 |
|------|------|------|
| IDE Compose（主线） | Coding Scaffold | 本仓 [`coding-scaffold/`](coding-scaffold/) |
| 刘海屏中枢 | 眉梢 / brew.app | [zhyr/brew](https://github.com/zhyr/brew) |
| 提示词 / 剪贴板树 | 栖痕 / Perch | [zhyr/Perch](https://github.com/zhyr/Perch) |
| Finder 路径复制 | 疏引 / Vestige | [zhyr/RightMenu](https://github.com/zhyr/RightMenu) |
| Agent 识别规范 | Al-exporter | [zhyr/Al-exporter](https://github.com/zhyr/Al-exporter) |
| 可选云端 | Forge / Sentinel | [haxitag.com/community/forge](https://haxitag.com/community/forge) |

详情、依赖方向与典型协作路径见 **[`TOOLCHAIN.md`](TOOLCHAIN.md)**。

---

## HaxiTAG Coding Scaffold（主线）

| 项 | 说明 |
|----|------|
| 定位 | 私有仓与 AI Coding 的对接插件（非编码 Agent 本体） |
| 主能力 | Compose Input：隐私清洗 → llint → 命名对齐 → 线性编排 → prompt；可选 Sentinel |
| 安装包 | [`coding-scaffold/dist/haxitag-coding-scaffold-0.5.3.vsix`](coding-scaffold/dist/haxitag-coding-scaffold-0.5.3.vsix)（版本以 `extension/package.json` 为准） |
| 说明 | [`coding-scaffold/README.md`](coding-scaffold/README.md) · 扩展详情 [`extension/README.md`](coding-scaffold/extension/README.md) |
| 官网 | [https://haxitag.com/community/forge](https://haxitag.com/community/forge) |

### 快速启用（Cursor）

```bash
# 1) 安装扩展
cursor --install-extension coding-scaffold/dist/haxitag-coding-scaffold-0.5.3.vsix

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

- **桌面配套仓与依赖方向**：→ **[`TOOLCHAIN.md`](TOOLCHAIN.md)**
- **根目录遗留脚本相对 Scaffold 的取舍**：→ **[`coding-scaffold/docs/05-kit-suite-integration.md`](coding-scaffold/docs/05-kit-suite-integration.md)**

结论摘要（仓内脚本）：`clean-data` 已并入 `tools/llint/doc_noise.py`；爬虫 / 书签阅读器 / 磁盘与 git 清理保持独立；根目录 `file_merger` / `structure-Explorer` **保持现状**（与 legacy 并存）。`disk_maintenance.sh` 另被 [brew](https://github.com/zhyr/brew) 集成。

---

## 仓库根目录其它工具（遗留 / 运维）

| 工具 | 用途 | 与 Scaffold |
|------|------|-------------|
| `data-for-llm-crawl.py` + `crawler_config.json` | 文档站爬取 → markdown | 可选旁路 ingest，不进扩展核心 |
| `clean-data.py` | 清洗爬虫产物噪声 | **已模块化**进 `coding-scaffold/tools/llint/doc_noise.py`（根脚本仍可离线写盘） |
| `file_merger.py` / `project-structure-Explorer.py` | 合并全文 / 目录树 | **保持现状**（根目录与 `tools/legacy/` 并存） |
| `universal-reader-*.html` | 网页 → markdown（浏览器） | 保持独立 |
| `js/vendor/` | showdown / mermaid / katex 等 | 半成品预览栈；Playground 见 Scaffold |
| `git-tidy.sh` / `disk_maintenance.sh` | 仓库 gc / 开发机清理 | 运维，不进 vsix；后者亦供 brew 引用 |
| token / `findIncorrectLinks.js` | 样例或历史 lint | 归档级 |

---

## 配套独立仓库（同系工具）

| 仓库 | 说明 |
|------|------|
| [眉梢 / brew.app](https://github.com/zhyr/brew) | macOS 刘海屏中枢（Atoll 二次开发）：应用启动器、AI agent 状态监控、磁盘维护（引用本仓 `disk_maintenance.sh`）、媒体控制；可一键唤起栖痕 |
| [栖痕 / Perch](https://github.com/zhyr/Perch) | macOS 菜单栏剪贴板 / 提示词记录管理器：按「记录树 + 分段」管理 LLM 上下文，可整树一键复制回喂；数据目录可指向 iCloud 多设备同步 |
| [疏引 / Vestige](https://github.com/zhyr/RightMenu) | Finder Sync：全局复制路径与文件名、批量复制、快捷打开终端，为非 IDE 场景提供项目文件引用入口 |
| [Al-exporter](https://github.com/zhyr/Al-exporter) | AI agent 安装路径与进程识别规范；brew 据此实现任务状态监控 |

关系图、协作路径与依赖方向：→ **[`TOOLCHAIN.md`](TOOLCHAIN.md)**。

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

- 工具链关系变更：先更新 [`TOOLCHAIN.md`](TOOLCHAIN.md)，再同步各配套仓 README。  
- 独立仓的协议与构建以各仓自身声明为准（例如 brew 为 GPL v3）。
