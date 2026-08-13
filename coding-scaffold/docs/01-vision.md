# 01 — 愿景：私有仓 × AI Coding 的「输入法」

## 一句话定位

`coding-scaffold` 是 **私有仓库与 AI Coding IDE / Agent 之间的对接插件**：在用户把内容交给模型 **之前**，自动整合出高质量的 **prompt + context**。

把它理解成 **输入前的自动整合输入法**——只做输入侧的清洗、对齐、增强与安检调用；**不**做成编码 Agent 本体，也 **不** 深绑某一家 IDE 的生命周期（如 Claude Hooks）。

## 宿主与协作方

| 角色 | 关系 |
|------|------|
| VS Code / Cursor / CodeBuddy 等 | 同一套扩展（vsix）安装运行；统一命令与 CLI |
| **Forge**（自有编码 Agent） | 下游消费者：吃 scaffold 产出的 prompt+context |
| **Sentinel**（自有安全 Agent） | 侧车调用：安全监测、供应链风险预警 |
| 私有仓 | 数据源；脱敏/清洗默认在内存注入路径，不污染源树主路径 |

## 能力边界（输入法该做的）

1. **数据注入**：选定文件/片段 → 策略过滤后注入上下文包  
2. **改写与增强**：面向模型的表述整理、结构补全（不替代业务编码）  
3. **参数 / 变量命名对齐**：与团队约定、schema、API 命名一致化  
4. **Linear / llint 清洗**：线性化与 lint 级噪声清理（进注入包）  
5. **调用 Sentinel**：安全监测、软件供应链风险预警（结果可附在注入包或侧栏）  
6. **策略闸门**：include/exclude、deny、体积上限——保证「能进模型的」干净可控  

产出形态固定为：**高质量 prompt + context（及可选安全附注）**。

## 明确不做（避免过度设计）

- 不实现 Forge / Sentinel 本体逻辑  
- 不深做单一厂商 Agent 钩子体系（Claude Hooks 等解决不了多 IDE）  
- 不做完整向量库 / 多租户云 Agent 网关 / 企业编码平台  
- 不为「脱敏」默认改写私藏原始源码（内存注入优先）  
- 不把整仓打成一个大 txt 当产品  

## 与历史脚手架

| 2024 legacy | 当前定位 |
|-------------|----------|
| path-annotator / 全文 merge | 降级；Compose 按需选片注入 |
| 早期 `cursor-prompt-*.txt`（已更名） | `haxitag-coding-prompt-*.txt` + `.cursor/rules` / Skills |
| 业务仓根目录脚本 | 抽成独立插件 + CLI，多 IDE 共用 |

## 成功标准

- 同一 vsix / CLI 可在 VS Code、Cursor、CodeBuddy 使用  
- 一次操作得到可粘贴/可交给 Forge 的 prompt+context  
- 可选一键调 Sentinel，预警进入附注而非另起平台  
- 文档与代码都不把 scaffold 写成「更深一层的 Agent」  
