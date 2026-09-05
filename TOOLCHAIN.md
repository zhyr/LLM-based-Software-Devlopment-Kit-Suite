# 工具链关系视图（Toolchain Map）

> 权威总览：本文件描述 **LLM-based Software Development Kit Suite** 与配套独立仓库的分工、依赖与典型协作路径。  
> 仓库内遗留脚本相对 Coding Scaffold 的取舍，见 [`coding-scaffold/docs/05-kit-suite-integration.md`](coding-scaffold/docs/05-kit-suite-integration.md)。

## 一句话

| 层 | 回答的问题 |
|----|------------|
| **Kit Suite（本仓）** | IDE 里怎么组 prompt / context？开发机怎么清垃圾、爬文档？ |
| **macOS 配套应用** | Finder / 刘海 / 剪贴板里怎么把路径与上下文接到 LLM 流程？ |
| **约定与规范** | 各 AI agent 装在哪、怎么识别是否在跑？ |

各仓可独立安装；组合使用时形成完整「取径 → 记录 → Compose → 调度 / 运维」链路。

### 命名约定

| 中文名 | 英文 / 产品名 | 仓库 |
|--------|---------------|------|
| **眉梢** | brew / `brew.app` | [zhyr/brew](https://github.com/zhyr/brew) |
| **栖痕** | Perch | [zhyr/Perch](https://github.com/zhyr/Perch) |
| **疏引** | Vestige / `Vestige.app` | [zhyr/RightMenu](https://github.com/zhyr/RightMenu) |

---

## 关系图

```text
                         ┌──────────────────────────────────────┐
                         │  Forge / Sentinel（可选云端策略）      │
                         │  https://haxitag.com/community/forge │
                         └──────────────────▲───────────────────┘
                                            │
┌───────────────────────────────────────────┴───────────────────────────────┐
│  LLM-based-Software-Devlopment-Kit-Suite（本仓库 · HaxiTAG 工具集）         │
│                                                                           │
│  ┌─────────────────────────────┐   ┌────────────────────────────────────┐ │
│  │ coding-scaffold（主线）      │   │ 根目录运维 / 遗留脚本               │ │
│  │ Compose prompt + context    │   │ disk_maintenance · git-tidy       │ │
│  │ llint / 隐私清洗 / Playground│   │ crawl · reader · file_merger …    │ │
│  └─────────────────────────────┘   └───────────────┬────────────────────┘ │
└────────────────────────────────────────────────────┼──────────────────────┘
                                                     │ 脚本被引用
                         ┌───────────────────────────▼──────────────────────┐
                         │  眉梢 brew.app  https://github.com/zhyr/brew     │
                         │  刘海屏中枢：启动器 · Agent 状态 · 磁盘清理 · 媒体 │
                         └───────────┬────────────────────▲─────────────────┘
                                     │ 唤起栖痕            │ 路径/进程约定
                         ┌───────────▼──────────┐  ┌──────┴─────────────────┐
                         │ 栖痕 Perch            │  │ Al-exporter            │
                         │ github.com/zhyr/Perch │  │ github.com/zhyr/Al-exporter │
                         │ 记录树 · 提示词回喂    │  │ Agent 安装/识别规范     │
                         └───────────▲──────────┘  └────────────────────────┘
                                     │ 粘贴路径/文件名
                         ┌───────────┴──────────┐
                         │ 疏引 Vestige          │
                         │ github.com/zhyr/RightMenu │
                         │ Finder：复制路径·终端  │
                         └──────────────────────┘
```

---

## 仓库一览

### 本仓（Kit Suite）

| 组件 | 路径 / 入口 | 角色 |
|------|-------------|------|
| **HaxiTAG Coding Scaffold** | [`coding-scaffold/`](coding-scaffold/) | 私有仓 × Cursor / VS Code / CodeBuddy：Compose Input（隐私清洗 → llint → 命名对齐 → 线性编排 → prompt） |
| **disk_maintenance.sh** | 仓库根 | 系统 / 开发者垃圾清理；被 **brew** 原样集成 |
| **git-tidy.sh** 等 | 仓库根 | 仓库 gc、运维；不进 vsix |
| 爬虫 / 阅读器 / merger | 仓库根 | 文档 ingest 旁路；相对 Scaffold 保持独立（见 05 文档） |

### 配套独立仓库（macOS / 规范）

| 产品 | 仓库 | 角色 | 与本仓关系 |
|------|------|------|------------|
| **眉梢 / brew.app** | [zhyr/brew](https://github.com/zhyr/brew) | 基于 Atoll 二次开发的刘海屏中枢；启动器、Agent 监控、磁盘清理、媒体 | 集成本仓 `disk_maintenance.sh`；监控约定来自 Al-exporter；Notes 委托栖痕 |
| **栖痕 / Perch** | [zhyr/Perch](https://github.com/zhyr/Perch) | 菜单栏剪贴板 / 提示词记录树，整树回喂 | 眉梢一键唤起；接收疏引复制的路径与文本 |
| **疏引 / Vestige** | [zhyr/RightMenu](https://github.com/zhyr/RightMenu) | Finder Sync：路径/文件名批量复制、打开终端 | 为 Scaffold / 对话 / 栖痕提供「全局取径」入口 |
| **Al-exporter** | [zhyr/Al-exporter](https://github.com/zhyr/Al-exporter) | AI agent 安装路径与进程识别规范 | brew 的 Agent 状态监控据此实现 |

### 上游（仅 brew）

brew 继承链（GPL v3）：`boring.notch` → `Atoll/DynamicIsland` → **眉梢 brew.app**。详见 [brew ReadMe](https://github.com/zhyr/brew/blob/main/ReadMe.md)。

---

## 典型协作路径

### A. 日常「把文件引用进 LLM」

1. Finder 选中文件 → **疏引** 复制路径或文件名（可 Shell 引号）  
2. 粘贴到 Chat / Agent，或先存入 **栖痕** 记录树  
3. 在 IDE 用 **Coding Scaffold → Compose Input** 整理 privacy + context 再开聊  

### B. 刘海屏工作台

1. **眉梢** 启动常用开发 app  
2. Agent 任务进行中：眉梢按 **Al-exporter** 约定显示 Trae / Cursor / Codex / WorkBuddy 等状态  
3. 需要记一笔：眉梢 → **栖痕**  
4. 磁盘吃紧：眉梢调用本仓集成的 **disk_maintenance**  

### C. 仅用本仓（无桌面 app）

安装 Coding Scaffold VSIX + 可选根目录脚本即可；不依赖眉梢 / 栖痕 / 疏引。

---

## 数据与依赖方向（摘要）

| 从 → 到 | 性质 |
|---------|------|
| Kit Suite `disk_maintenance.sh` → 眉梢 | **脚本集成**（原样拷贝 + Swift 封装） |
| Al-exporter → 眉梢 | **约定引用**（路径/进程识别，非 submodule） |
| 眉梢 → 栖痕 | **进程唤起**（`NSWorkspace` 打开外部 app） |
| 疏引 → 栖痕 / Scaffold / 任意 LLM | **剪贴板文本**（无硬依赖） |
| Scaffold → Forge / Sentinel | **可选**云端策略 |

疏引、栖痕、Scaffold **互不强制安装**；眉梢在栖痕未安装时回退内置 Clipboard tab。

---

## 维护约定

- **关系变更**（新增同系仓库、改依赖方向）：先改本文件，再同步各仓 README 中的「工具链」小节。  
- **本仓脚本 vs Scaffold**：仍以 [`05-kit-suite-integration.md`](coding-scaffold/docs/05-kit-suite-integration.md) 为准。  
- 各独立仓的构建、签名、协议以**该仓自身 README / LICENSE** 为准（例如 brew 为 GPL v3）。
