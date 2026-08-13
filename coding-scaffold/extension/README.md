# HaxiTAG Coding Scaffold

私有仓库与 AI Coding IDE / Agent 的对接扩展：在内容进入对话前，整理出高质量的 **prompt + context**。

适用于 **VS Code、Cursor、CodeBuddy**；可配合 [Forge · 智能软件工厂](https://haxitag.com/community/forge) 使用。源仓默认只读，脱敏与清洗在内存中完成，不写回私藏源码。

---

## 功能

| 能力 | 说明 |
|------|------|
| **Compose Input** | 一键整合：隐私清洗 → llint（含文档噪声）→ 命名对齐 → 线性编排 → prompt 壳 |
| **动态注入** | 选定文件内存脱敏/去噪后注入上下文，不写回源文件 |
| **命名对齐** | 按 `.haxitag/naming-align.yaml` 统一参数/变量名 |
| **Sentinel 桥** | 可选安全/供应链预检附注（对接自有 Sentinel） |
| **策略闸门** | `workspace-policy.yaml` 控制可读范围与禁止项 |

产出可粘贴进 Chat / Agent，或交给 Forge 继续实现。本扩展**不是**编码 Agent 本体，也不会自动接管 Cursor Agent。

---

## 启用指南（三步）

目前通过 **本地 vsix** 安装（扩展市场通常搜不到）。本机需有 `python3`。

### 1. 安装扩展

在仓库中找到打包产物（见下方「打包」），例如：

`coding-scaffold/dist/haxitag-coding-scaffold-0.5.3.vsix`

**Cursor**

```bash
cursor --install-extension /绝对路径/coding-scaffold/dist/haxitag-coding-scaffold-0.5.3.vsix
```

或：Cursor → Extensions → `⋯` → **Install from VSIX…** → 选择该文件 → **Reload**。

**VS Code / CodeBuddy**

```bash
code --install-extension /绝对路径/coding-scaffold/dist/haxitag-coding-scaffold-0.5.3.vsix
```

或在对应 IDE 的扩展面板选择 **Install from VSIX…**。

确认：扩展列表搜索 `HaxiTAG`；Cursor 聊天可用 `@installed HaxiTAG`。

### 2. 准备私有仓工作区

在 `coding-scaffold` 目录执行（把策略与 rules 写入目标仓）：

```bash
cd coding-scaffold
python3 tools/policy/bootstrap_workspace.py \
  --root /你的/私有仓路径 \
  --profile local-dev
```

用 Cursor（或 VS Code / CodeBuddy）**打开该私有仓**作为工作区。

### 3. 日常使用 Compose

1. 在资源管理器选中文件/文件夹，或打开编辑器中的文件  
2. `Cmd+Shift+P`（Windows：`Ctrl+Shift+P`）→ 运行 **`HaxiTAG: Compose Input (prompt + context)`**  
   - 也可在资源管理器 / 编辑器右键使用同名命令  
3. 可选填写任务描述，并选择是否附带 Sentinel 预检  

生成的 Markdown 会打开并复制到剪贴板 → **粘贴进 Chat / Agent**。

仅需隐私层注入时，使用 **`HaxiTAG: Inject Sanitized Context only`**。

---

## 命令一览

- **Compose Input (prompt + context)** — 主入口  
- **Inject Sanitized Context only** — 仅隐私注入  
- **Structure Explorer** — 目录树（诊断）  
- **Open coding prompt template** — 打开 `haxitag-coding-prompt-*.txt`  
- **Open Markdown Playground** / **Open Mermaid Playground** — 本地预览页  
- Path Annotate / Context Builder — Legacy（会写盘，需二次确认）

## Playground（Markdown / Mermaid）

扩展 **Details 页只能显示静态 README**，无法内嵌交互预览。请用命令打开本地页：

| 入口 | 命令 / 文件 |
|------|-------------|
| Markdown | `HaxiTAG: Open Markdown Playground` → `playground/markdown.html` |
| Mermaid | `HaxiTAG: Open Mermaid Playground` → `playground/mermaid.html` |

也可直接用浏览器打开仓库内上述 HTML。适合预览 Compose 产出或画流程草图。

### CLI（与扩展同源，可选）

```bash
cd coding-scaffold
python3 tools/inject/compose_input.py \
  --root /path/to/private-repo \
  --policy /path/to/private-repo/.haxitag/workspace-policy.yaml \
  --files src/a.ts \
  --task "你的任务" \
  --sentinel
```

---

## 打包（维护者）

在 `coding-scaffold` 下执行：

```bash
cd coding-scaffold/extension
npm install          # 首次或依赖变更时
npm run package:vsix
```

或从项目根目录：

```bash
cd coding-scaffold
npm run extension:package
```

流程说明：

1. `prepare-resources` — 同步 Python 工具、策略模板，并从 `docs/codingscoffold.png` 生成 `media/icon.png`  
2. `compile` — 编译 TypeScript  
3. 打出 vsix（优先 vsce；失败则 zip 回退）  

产物位置：

- `coding-scaffold/extension/haxitag-coding-scaffold-<version>.vsix`  
- 同时复制到 `coding-scaffold/dist/haxitag-coding-scaffold-<version>.vsix`  

改版本号：编辑 `extension/package.json` 的 `version` 字段后再打包。当前版本见该文件。

---

## 要求

- 本机 `python3`  
- 建议工作区含 `.haxitag/workspace-policy.yaml`（可用 bootstrap 生成）

## 链接

- 官网 / Forge：[https://haxitag.com/community/forge](https://haxitag.com/community/forge)  
- 源码：[LLM-based-Software-Devlopment-Kit-Suite](https://github.com/zhyr/LLM-based-Software-Devlopment-Kit-Suite) → `coding-scaffold/`

---

© HaxiTAG 哈希泰格
