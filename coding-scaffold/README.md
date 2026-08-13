# HaxiTAG Coding Scaffold

本目录是 **独立管理的源码项目**（仍放在 [LLM-based-Software-Devlopment-Kit-Suite](https://github.com/zhyr/LLM-based-Software-Devlopment-Kit-Suite) 仓库内）。

**定位**：私有仓库与 AI Coding IDE / Agent 的对接插件——**输入前的自动整合输入法**。  
同一套 vsix/CLI 可在 **VS Code、Cursor、CodeBuddy** 安装运行；产出交给 Forge（自有编码 Agent）等下游；安全侧调用 **Sentinel**（监测 / 供应链预警）。

能力面：数据注入、改写增强、参数变量命名对齐、Linear / llint 清洗、Sentinel 调用 → **高质量 prompt + context**。  
不做编码 Agent 本体，不深绑单厂商 hooks。

> 脱敏/清洗默认走 **内存注入**（源仓只读主路径）。Legacy 路径注释 / 整仓 merge 仅保留兼容。

## 历史沿革

| 时间 | 阶段 | 说明 |
|------|------|------|
| **2024-07** | 上下文管理萌芽 | [HaxiTAG-Assistant](https://github.com/zhyr/HaxiTAG-Assistant) 浏览器插件：本地管理 instruction / context，向 ChatGPT、Claude、Kimi 等页面插入（与编码仓脚手架同源问题意识，但宿主是浏览器） |
| **2024-09 ~ 10** | Kit-Suite 立库 | [LLM-based-Software-Devlopment-Kit-Suite](https://github.com/zhyr/LLM-based-Software-Devlopment-Kit-Suite) 仓库创建；收录 crawler、清洗、structure explorer、file merger 等「给 LLM 备料」工具 |
| **2024-11 ~ 12** | 嵌在业务仓的脚手架 | 工具深入业务仓：`haxitag-path-annotator` / `structure-Explorer` / `context-builder`、多语言抽取、早期 `cursor-prompt-*`（现已更名为 `haxitag-coding-prompt-*`）/ CoT 模板 |
| **2024 末 ~ 2025** | 本地 vsix 尝试 | 计划把上述脚本打成 `haxitag-coding-scaffold` VS Code / Cursor 扩展；**产物未进入 git**，本机/Release 侧亦未找回原始 `.vsix` |
| **2025 ~ 2026 上** | 能力被 Agent 稀释 | Cursor / Claude Code 等本机 Agent 普及后：路径感知、目录遍历、按需读文件成为默认能力；「文件头插路径」「整仓合并成一个 txt」对日常编码价值大降 |
| **2026-08** | 抽离 + 动态注入 | 建立 `coding-scaffold/`：legacy 隔离；主线 **策略 + validate/bootstrap + `resolve_context` 内存注入**；扩展 `0.3.0`（Inject Sanitized Context） |

能力演进一句话：

```text
网页 chatbot 拼 prompt
  → 业务仓根目录 Python 脚手架 + Cursor 提示词
    → 本机 Agent 原生上下文
      → 企业私有仓：策略边界 + 脚手架动态清理/注入（源仓只读）
```

## 目录结构

```text
coding-scaffold/
├── README.md
├── package.json
├── docs/
├── tools/
│   ├── inject/               # compose_input（主入口）+ resolve_context
│   ├── llint/ align/ enhance/ sentinel/  # Compose 薄模块
│   ├── privacy/              # 内存流水线 + 扫描报告
│   └── policy/               # bootstrap / validate
├── prompts/                  # haxitag-coding-prompt-*.txt（宿主无关）
├── enterprise/
├── extension/                # VS Code / Cursor / CodeBuddy 同源 vsix
├── examples/
└── dist/
```

## 快速开始

### AI 编码：整合输入（推荐主入口）

```bash
cd coding-scaffold

python3 tools/policy/bootstrap_workspace.py \
  --root /path/to/your-private-repo \
  --profile local-dev

# 输入法：privacy → llint → align → linear → enhance →（可选）Sentinel
python3 tools/inject/compose_input.py \
  --root /path/to/your-private-repo \
  --policy /path/to/your-private-repo/.haxitag/workspace-policy.yaml \
  --files src/a.ts src/b.ts \
  --task "修复登录校验" \
  --format markdown \
  --sentinel
```

扩展命令（VS Code / Cursor / CodeBuddy）：**HaxiTAG: Compose Input (prompt + context)**。  
仅隐私注入可用 `resolve_context.py` / **Inject Sanitized Context only**。

产出为稳定 pack（`schema: haxitag.coding-scaffold.pack`），可粘贴给 Agent 或交给 Forge。

### 策略校验 / 隐私扫描（不改源）

```bash
python3 tools/policy/validate_workspace.py \
  --root /path/to/your-private-repo \
  --policy enterprise/profiles/local-dev.example.yaml

python3 tools/privacy/redact_workspace.py \
  --root /path/to/your-private-repo \
  --policy /path/to/your-private-repo/.haxitag/workspace-policy.yaml \
  --report /tmp/privacy-report.json
```

### Legacy（可选，慎用）

```bash
python3 tools/legacy/haxitag-structure-Explorer.py -d /path/to/repo
# path-annotator / context-builder 会写文件，新项目不推荐
```

### 扩展打包

```bash
cd extension && npm install && npm run package:vsix
# 产物：../dist/haxitag-coding-scaffold-*.vsix
```

## 文档

| 文档 | 内容 |
|------|------|
| [docs/01-vision.md](docs/01-vision.md) | 定位与边界 |
| [docs/02-architecture.md](docs/02-architecture.md) | Compose 架构 |
| [docs/03-roadmap.md](docs/03-roadmap.md) | 路线图 |
| [docs/04-privacy-kb-alignment.md](docs/04-privacy-kb-alignment.md) | 隐私对齐 |
| [docs/05-kit-suite-integration.md](docs/05-kit-suite-integration.md) | 根目录工具集成分析 + Playground |
| [prompts/README.md](prompts/README.md) | `haxitag-coding-prompt-*` 命名 |
| [playground/](playground/) | Markdown / Mermaid 预览页 |
| [enterprise/README.md](enterprise/README.md) | 策略与模板 |
| [tools/legacy/README.md](tools/legacy/README.md) | 旧工具状态 |

## 设计原则

1. **对接层，非 Agent**：只做到输入前整合；Forge / 各 IDE 负责更深运行时。
2. **多 IDE 同源**：vsix + CLI，不依赖单厂商 Hooks。
3. **源仓只读主路径**：脱敏/llint 进注入包；不默认改写私藏源码。
4. **侧车 Sentinel**：安全与供应链预警可附注，本体不在本仓。
5. **策略先于拼装**：能进模型的路径先过 policy。
6. **提示词宿主无关**：统一 `haxitag-coding-prompt-*`，不绑 Cursor 等品牌前缀。
7. **Legacy 隔离**：旧写盘脚本不作为新扩展点。
