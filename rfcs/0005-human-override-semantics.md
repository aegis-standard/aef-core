# AEF-RFC-0005: Human Override Semantics

状态：DRAFT
日期：2026-05-16
作者：AEGIS Steering Committee
依赖：RFC-0001 (Event Core Schema)
关联：RFC-0002 (Replay Semantics), RFC-0003 (Interrupt Semantics)

---

## 1. Abstract

定义 AEF 生态中“人类覆盖 (Human Override)”的精确语义。人类覆盖是指人类操作者显式修改 Agent 输出或决策的行为。此 RFC 规定覆盖事件的必需字段、覆盖对确定性链的影响、覆盖与中断的关系，以及覆盖在回放中的处理规则。

## 2. Motivation

人类覆盖是 AI 行为中最高权重的信号。它携带了人类的隐性判断、风险偏好和美学标准。如果在证据层不精确记录覆盖行为，审计将无法区分“AI 自己做的”和“人让 AI 做的”，责任归属将彻底模糊。

## 3. Human Override Event Definition

### 3.1 事件类型

| action | 含义 |
|--------|------|
| `human.override` | 人类显式覆盖了 Agent 的输出或决策 |

此事件是 AEF 中唯一的 `actor = "human"` 且 `action` 不是元操作的事件类型。

### 3.2 必需字段

`human.override` 的 `payload` 必须包含以下三个字段：

| 字段 | 类型 | 含义 |
|------|------|------|
| `original_output` | string | Agent 原始输出（被覆盖前的完整内容） |
| `corrected_output` | string | 人类修改后的输出 |
| `override_reason` | string | 人类说明为什么覆盖（如“方向偏离”、“数据错误”、“风格不符”） |

### 3.3 可选字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `override_scope` | string | 覆盖范围：`full`（完全替换）或 `partial`（部分修改）。默认 `full` |
| `related_event_id` | string | 被覆盖的 Agent 输出所在的事件 id |

## 4. Override as Determinism Break

### 4.1 确定性中断

`human.override` 事件**中断**当前因果链的确定性。因为人类的覆盖行为不可通过算法重现，覆盖点之后的所有事件在回放时的处理方式与覆盖前不同。

### 4.2 因果链处理

- `human.override` 的 `causality_id` 指向触发覆盖的 Agent 输出事件
- 覆盖之后的第一个 Agent 事件的 `causality_id` 指向 `human.override`
- 覆盖点前后的因果链分别验证确定性，覆盖点本身作为分界线

### 4.3 回放处理

根据 RFC-0002，回放至 `human.override` 时：
- 回放 Runtime 必须使用 `corrected_output` 作为后续执行的输入
- 不得重新执行被覆盖的 Agent 行为（因为人类判断不可重现）
- 回放结果中 `conditions.human_override_acknowledged` 标记为 `true`

## 5. Override and Interrupt

### 5.1 关系

覆盖和中断是两个独立的行为，但可能同时发生：

| 场景 | 事件序列 |
|------|---------|
| 仅覆盖 | `agent.call.completed` → `human.override` → 继续执行 |
| 仅中断 | `...` → `agent.interrupted` → `agent.interrupt.resolved` → `...` |
| 覆盖后中断 | `human.override` → `agent.interrupted` → `agent.interrupt.resolved` → 使用覆盖后输出继续 |
| 中断中覆盖 | `agent.interrupted` → `human.override` → `agent.interrupt.resolved` |

### 5.2 同时发生时的优先级

如果 `human.override` 和 `agent.interrupted` 在同一因果点发生，覆盖优先处理——先记录 `human.override`，再处理中断。

## 6. Override Chain

### 6.1 多次覆盖

如果同一输出被多次覆盖，每次覆盖产生独立的 `human.override` 事件，形成覆盖链。

### 6.2 验证规则

覆盖链中每个后续 `human.override` 的 `original_output` 应是前一个覆盖的 `corrected_output`。

## 7. Immutability Clause

此 RFC 中第 3 节定义的覆盖事件必需字段（`original_output`、`corrected_output`、`override_reason`）自冻结之日起永不删除或修改其语义。第 4 节定义的覆盖中断确定性规则永不变更。

## 8. References

- RFC-0001: Event Core Schema
- RFC-0002: Replay Semantics
- RFC-0003: Interrupt Semantics