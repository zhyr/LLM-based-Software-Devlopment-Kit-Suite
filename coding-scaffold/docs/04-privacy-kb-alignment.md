# 04 — 隐私与脱敏：对齐 KnowledgeBase（动态注入）

## 原则

**禁止**为了清洗 / 去噪 / 脱敏去修改私藏原始代码。  
在 AI coding 中 **引用 coding-scaffold**，对选定文件做 **内存流水线**，再把结果 **注入** Agent 上下文。

## 参考源（HaxiTAG-AI-CMS）

| 位置 | 作用 | 本项目落地 |
|------|------|------------|
| KnowledgeBuilder / SynthesisAugmentation | 「脱敏」「去噪」勾选 | `privacy.methods` |
| `preprocess.ts` | 卡号 / email / phone / id 打码 | `tools/privacy/anonymize.py` |
| `logger.ts` | `SENSITIVE_KEYS` → `***REDACTED***` | `tools/privacy/sanitize.py` |

## 流水线

```text
私有仓文件 (READ-ONLY)
  → 清洗 (clean) → 去噪 (denoise) → 脱敏 (redact)   [内存]
  → Inject pack (markdown / json) → Agent
```

## CLI（主线：整合输入）

```bash
python3 tools/inject/compose_input.py \
  --root /path/to/private-repo \
  --policy /path/to/private-repo/.haxitag/workspace-policy.yaml \
  --files src/a.ts \
  --task "…" \
  --format markdown \
  --sentinel
```

流水线：privacy → llint → align → linear → enhance →（可选）Sentinel。  
扩展：`HaxiTAG: Compose Input`。仅隐私层：`resolve_context.py`。

## CLI（扫描报告，不改源）

```bash
python3 tools/privacy/redact_workspace.py \
  --root /path/to/private-repo \
  --policy ... \
  --report /tmp/privacy-report.json
```

## 策略字段

`privacy.mode`：`inject`（默认）| `report`  
`methods` / `sensitiveKeys` / `piiFieldKeys` / `noiseGlobs` 等见 schema。
