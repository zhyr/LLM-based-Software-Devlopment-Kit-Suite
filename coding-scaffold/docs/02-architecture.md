# 02 — 架构：输入前整合层

```text
Private repo (read-mostly)
        │
        ▼
┌──────────────────────────────────────────────┐
│ compose_input（输入法）                        │
│ privacy → llint → align → linear → enhance   │
│ (+ optional Sentinel bridge)                 │
└───────────────────┬──────────────────────────┘
                    │ pack v1: prompt + context + security?
                    ▼
     VS Code / Cursor / CodeBuddy / Forge
```

| 模块 | 路径 |
|------|------|
| Compose | `tools/inject/compose_input.py` |
| Privacy inject | `tools/inject/resolve_context.py` |
| llint / linear | `tools/llint/` |
| align | `tools/align/` + `.haxitag/naming-align.yaml` |
| enhance | `tools/enhance/` |
| Sentinel bridge | `tools/sentinel/` |
| Pack schema | `enterprise/schemas/compose-pack.v1.json` |
| Extension | `extension/`（Compose Input） |

Sentinel：默认本地供应链/密钥启发式预检；`sentinel.command` / `SENTINEL_CMD` / `SENTINEL_URL` 接完整 [Sentinel](https://github.com/zhyr/Sentinel)。不内嵌安全 Agent。
