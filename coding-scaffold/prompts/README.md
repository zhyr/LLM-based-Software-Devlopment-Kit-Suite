# prompts/

HaxiTAG Coding Scaffold 官方提示词模板（宿主无关命名）。

| 文件 | 用途 |
|------|------|
| `haxitag-coding-prompt-1-ts-node.txt` | TypeScript / Node 编码约定 |
| `haxitag-coding-prompt-2-chrome.txt` | Chrome / 浏览器扩展相关 |
| `haxitag-coding-prompt-3-inference.txt` | 推理 / 分析类任务 |
| `haxitag-coding-prompt-4-cot.txt` | Chain-of-Thought 模板 |
| `haxitag-coding-prompt-5-coding.txt` | 通用编码补充 |
| `haxitag-coding-prompt-6-coding.txt` | 通用编码主模板 |

扩展命令 **Open coding / CoT prompt template** 从本目录（打包后为 `resources/prompts/`）读取。

## 命名约定

统一前缀：`haxitag-coding-prompt-<n>-<topic>.txt`

- **不**使用 `cursor-prompt-*`：产品同时服务 VS Code / Cursor / CodeBuddy / Forge，提示词与 IDE 品牌正交。
- 历史别名（2024）：`cursor-prompt-1-…` ~ `cursor-prompt-6-…` / `Cursor-prompt-4-CoT.txt` → 已迁入上表。

`rules/` 为可复用 Agent rules 片段；企业落地以 `enterprise/templates/` 为准。
