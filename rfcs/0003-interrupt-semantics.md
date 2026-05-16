# AEF-RFC-0003: Interrupt Semantics

状态：DRAFT
日期：2026-05-16
作者：AEGIS Steering Committee
依赖：RFC-0001 (Event Core Schema)
关联：RFC-0002 (Replay Semantics)

---

## 1. Abstract

定义 AEF 生态中“中断 (Interrupt)”的精确语义。中断是指由系统或人类主动发起的、导致当前执行流程提前终止或暂停的行为。此 RFC 规定中断事件的边界、中断对因果链和可回放性的影响，以及中断恢复的规则。

## 2. Motivation

在长时间运行的 Agent 任务中，中断是常态而非例外。如果中断的语义不清晰，回放可能产生歧义，审计也无法确认“中断那一刻到底发生了什么”。此 RFC 的目标是消除这种模糊性。

## 3. Interrupt Event Definition

### 3.1 事件类型

中断事件使用标准 AEF action 类型：

| action | 含义 |
|--------|------|
| `agent.interrupted` | Agent 执行被中断（系统或人类发起） |
| `agent.interrupt.resolved` | 中断被恢复，执行继续 |
| `agent.error` | 执行因错误终止（不可恢复） |

### 3.2 必需字段

- `agent.interrupted` 的 `payload` 必须包含：
  - `reason`: string — 中断原因（如 `timeout`, `human_request`, `resource_exhausted`）
  - `source`: "system" | "human" — 中断来源
- `agent.interrupt.resolved` 的 `payload` 必须包含：
  - `resumed_from_event_id`: string — 中断前最后一个成功事件的 id

## 4. Interrupt Boundary (中断边界)

中断边界由一对事件界定：

[上一个成功事件] → agent.interrupted → [可选等待期] → agent.interrupt.resolved → [下一个事件]


### 4.1 中断期间的 Causality

- `agent.interrupted` 的 `causality_id` 指向中断发生前最后一个成功事件
- `agent.interrupt.resolved` 的 `causality_id` 指向 `agent.interrupted`
- 中断本身**不产生**工具调用或推理事件，它是元事件

### 4.2 中断对 Replay 的影响

根据 RFC-0002，回放时遇到 `agent.interrupted`：

- 如果后续有 `agent.interrupt.resolved`，回放 Runtime 应等待（模拟等待），但实际执行的确定性组件必须从中断前的状态恢复
- 如果中断后直接是 `agent.error`（即未恢复），回放可以标记为 `partial_replay: true`，仅回放至中断前的事件序列

## 5. Interrupt vs. Error

| | Interrupt | Error |
|------|-----------|-------|
| 是否可恢复 | 是（通过 `agent.interrupt.resolved`） | 否（会话终止） |
| 对因果链的影响 | 暂停，保留链完整性 | 终止，链在此结束 |
| 回放处理 | 可回放至中断点，或恢复后继续 | 仅回放至错误前最后一个事件 |

## 6. Human-Triggered Interrupt

当 `source = "human"` 时，`agent.interrupted` 表示人类主动暂停执行。这种中断不破坏确定性链，因为人类意图是系统行为的一部分。人类中断可能伴随 `human.override`（参见 RFC-0005），但并非必然。

## 7. Edge Cases

### 7.1 Nested Interrupts

不支持嵌套中断。如果一个 `agent.interrupted` 之后再次中断，Runtime 应将其视为同一个中断区间，不产生新的 `agent.interrupted` 事件。

### 7.2 Interrupt During Tool Call

如果中断发生在工具调用执行期间，Runtime 必须：
1. 允许当前工具调用完成（如果资源允许），然后发送 `agent.interrupted`
2. 如果无法等待工具调用完成（如强制终止），工具调用产生 `tool.call.error`，紧接着发送 `agent.interrupted`

## 8. Immutability Clause

此 RFC 中第 3 节定义的中断事件类型、第 4 节定义的中断边界和第 5 节定义的中断与错误的区别自冻结之日起永不修改。

## 9. References

- RFC-0001: Event Core Schema
- RFC-0002: Replay Semantics
- RFC-0005: Human Override Semantics (DRAFT)