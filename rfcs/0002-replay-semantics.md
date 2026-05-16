# AEF-RFC-0002: Replay Semantics

状态：DRAFT
日期：2026-05-16
作者：AEGIS Steering Committee
依赖：RFC-0001 (Event Core Schema)

---

## 1. Abstract

定义 AEF 生态中“合法回放 (Valid Replay)”的充要条件。一次合法回放必须满足：事件顺序完全一致、因果链完整可重建、工具调用结果在确定容差范围内。此定义是审计、合规、法律证据可采性的技术基石。

## 2. Motivation

AEF 的核心价值在于证明“AI 行为真实发生”。如果回放的定义不稳定，审计报告在法庭上就不具备可信度。此 RFC 的目标是给出一个精确、可自动验证、跨 Runtime 通用的“合法回放”标准。

## 3. Definition of Valid Replay

一次合法回放，指对于给定的 `session_id`，将原始 AEF 事件流 (E₁, E₂, ..., Eₙ) 在一个符合 AEF 的 Runtime 中按顺序重新执行，并产生验证结果 R。

R 为 `VALID` 当且仅当以下三个条件**全部**满足：

### 3.1 Event Order Preserved (事件顺序不变)

重新执行时，事件产生的顺序必须与原始事件流完全一致。

验证规则：逐事件比对 `action` 类型序列。若序列出现重排、缺失、多出，条件不满足。

### 3.2 Causality Chain Intact (因果链完整)

所有事件的 `causality_id` 必须在原始事件流中形成完整的单向无环链。

验证规则：
- 对每个事件的 `causality_id`，必须在其之前存在该 `id` 对应的事件
- `causality_id = null` 只能出现在会话的第一个事件
- 禁止循环引用（事件 A 指向 B，B 又指向 A）

### 3.3 Deterministic Component Match (确定性组件匹配)

对于被标记为 `deterministic = true` 的事件组件，其重新执行产生的值必须与原始值匹配。

#### 3.3.1 确定性组件定义

以下组件被定义为确定性组件：

| 组件 | 说明 | 验证方式 |
|------|------|----------|
| `tool.call.started` 的 `input` | 工具调用入参 | 深度值比对 |
| `tool.call.completed` 的 `output` | 工具调用出参 | 深度值比对 |
| `integrity_hash` | 事件完整性哈希 | SHA-256 比对 |

以下组件被定义为非确定性组件（不参与回放匹配）：

| 组件 | 说明 | 原因 |
|------|------|------|
| LLM 推理的文本输出 | Agent 推理内容 | 模型升级、温度导致差异 |
| `timestamp` 字段 | 事件发生时间 | 回放在不同时间进行 |

#### 3.3.2 容差规则

对于确定性组件，采用以下容差规则：

| 数据类型 | 容差 | 说明 |
|----------|------|------|
| 字符串 | 精确匹配 | 任何字符差异视为不匹配 |
| 数字 (float) | `abs(orig - replay) ≤ 1e-6` | 浮点精度容差 |
| 数字 (int) | 精确匹配 | |
| 布尔 | 精确匹配 | |
| 数组 | 长度一致 + 逐元素按本表规则匹配 | 顺序敏感 |
| 对象 | 键集合一致 + 逐键按本表规则匹配 | 多出/缺少键视为不匹配 |

## 4. Replay Result Object

每次回放必须产出以下结构的结果对象：

```yaml
replay_result:
  session_id: string
  replayed_at: string (ISO 8601)
  replay_runtime: string    # 执行回放的 Runtime 名称与版本
  status: "VALID" | "INVALID"
  conditions:
    event_order_preserved: true | false
    causality_chain_intact: true | false
    deterministic_match: true | false
  details:
    first_mismatch_event_id: string | null
    mismatch_description: string | null
  original_event_count: int
  replayed_event_count: int

  5. Edge Cases
5.1 Interrupted Sessions
如果原始会话以 agent.error 或 interrupt 事件结束，回放可以仅针对已完成的事件序列进行。回放结果中需标注 partial_replay: true。

5.2 Human Override
human.override 事件中断确定性链（参见 RFC-0005）。回放至 human.override 时，回放 Runtime 应使用原始事件的 corrected_output 继续，而非重新执行被覆盖的 Agent 行为。

5.3 Tool Non-Determinism
部分工具（如调用外部 API、读取实时数据）天然具有非确定性。此类工具应在 AEF Tool Registry 中标记为 deterministic = false。标记为非确定性的工具调用，其 output 不参与 3.3 的条件判定。

6. Immutability Clause
此 RFC 中 3.1、3.2、3.3 定义的合法回放三条件自冻结之日起永不修改。3.3.2 的容差规则在需要时可通过新 RFC 编号扩展（如定义 float64_loose 容差），但不得修改或削弱当前已定义的 default 容差。

7. References
RFC-0001: Event Core Schema

RFC-0004: Tool Invocation Semantics (DRAFT)

RFC-0005: Human Override Semantics (DRAFT)