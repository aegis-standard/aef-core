# AEF-RFC-0006: Determinism Guarantees

状态：DRAFT
日期：2026-05-16
作者：AEGIS Steering Committee
依赖：RFC-0001 (Event Core Schema)
关联：RFC-0002 (Replay Semantics), RFC-0004 (Tool Invocation Semantics)

---

## 1. Abstract

定义 AEF 生态中“确定性执行 (Deterministic Execution)”的分级标准和技术要求。确定性是指对于相同的输入和初始状态，执行过程总是产生完全相同的事件序列和输出。此 RFC 定义 L0 到 L4 五个确定性等级，每级对应不同的技术保证和适用场景。

## 2. Motivation

确定性是回放可信的前提。如果执行本身不可重现，任何审计结论都将失去根基。但并非所有场景都需要最高等级的确定性。此 RFC 的目标是提供一套分级标准，让不同场景可以选择适合的确定性等级，同时保持术语和判定的统一。

## 3. Determinism Levels

### 3.1 等级总览

| 等级 | 名称 | 一句话定义 |
|------|------|-----------|
| L0 | 无保证 | 执行结果可能因任何因素而变化 |
| L1 | 事件结构确定 | 事件类型和顺序确定，但内容可变 |
| L2 | 工具调用确定 | L1 + 确定性工具调用的输入输出完全一致 |
| L3 | 因果链确定 | L2 + 因果链在所有回放中完全一致 |
| L4 | 字节级确定 | L3 + 所有事件内容逐字节一致（不含非确定性字段） |

### 3.2 各等级详细定义

#### L0 — No Guarantees (无保证)

- 不提供任何确定性保证
- 适用于：原型开发、探索性任务
- 回放可能产生完全不同的结果

#### L1 — Event Structure Determinism (事件结构确定)

必须满足：
- 同一会话回放产生相同数量的同类型事件
- `action` 类型序列完全一致
- 允许事件 `payload` 内容差异

适用于：基本审计、流程合规检查

#### L2 — Tool Call Determinism (工具调用确定)

必须满足 L1 的全部条件，加上：
- 所有标记为 `deterministic = true` 的工具调用，其 `input` 和 `output` 在回放中精确匹配（按 RFC-0004 和 RFC-0002 的容差规则）
- 非确定性工具调用的输出允许差异

适用于：工具链审计、自动化测试

#### L3 — Causality Chain Determinism (因果链确定)

必须满足 L2 的全部条件，加上：
- 所有事件的 `causality_id` 关系在回放中完全一致
- 因果图（事件节点和边的集合）同构

适用于：责任追溯、多 Agent 协作审计

#### L4 — Byte-Level Determinism (字节级确定)

必须满足 L3 的全部条件，加上：
- 所有事件的内容（排除显式标记为非确定性的字段）逐字节一致
- 事件的 `integrity_hash` 在所有回放中完全相同

排除在 L4 比较范围外的字段：
- `timestamp`（时间戳）
- `metadata.tags`（标签可增删）
- 非确定性工具调用的 `output`

适用于：法庭证据、高安全合规、密码学验证

## 4. Deterministic vs Non-Deterministic Components

### 4.1 确定性组件

| 组件 | 说明 |
|------|------|
| 工具调用入参 (`tool.call.started.input`) | 由 Agent 决策产生，回放时决策逻辑应一致 |
| 工具调用出参 (`tool.call.completed.output`) | 仅限 `deterministic = true` 的工具 |
| 事件类型序列 | 由执行逻辑决定 |
| 因果链结构 | 由任务拆解和执行顺序决定 |

### 4.2 非确定性组件

| 组件 | 说明 |
|------|------|
| LLM 推理文本 | 模型版本、采样参数导致差异 |
| 外部 API 调用结果 | 外部状态不可控 |
| `timestamp` | 回放在不同时间执行 |
| 系统资源指标 | 内存、CPU 使用量等运行时状态 |

## 5. Determinism Declaration

每个声称符合 AEF 的 Runtime 必须在首次输出事件时声明其支持的最高确定性等级：

```yaml
runtime_capability:
  name: string
  version: string
  max_determinism_level: "L0" | "L1" | "L2" | "L3" | "L4"

  此声明写入会话的第一个事件的 metadata.runtime_capability 中。

6. Verification
6.1 等级验证
确定性等级由 AEF Compliance Suite 自动测试判定。验证方法：

L1：回放 10 次，检查事件类型序列一致性

L2：L1 测试 + 100 个确定性工具调用回放匹配

L3：L2 测试 + 因果图同构检查

L4：L3 测试 + 逐事件完整性哈希比对

6.2 等级降级
如果 Runtime 在回放中无法满足声明等级的测试，其认证等级自动降级为实际达到的最高等级。

7. Immutability Clause
此 RFC 中第 3 节定义的 L0-L4 等级名称和层级关系自冻结之日起永不修改。各等级的技术要求在需要时可通过新 RFC 编号加严（如 L4 增加新比对项），但不得放宽已冻结的要求。

8. References
RFC-0001: Event Core Schema

RFC-0002: Replay Semantics

RFC-0004: Tool Invocation Semantics

RFC-0007: Compliance Levels (DRAFT)