
---

## RFC-0007 完整内容（直接复制）

```markdown
# AEF-RFC-0007: Compliance Levels

状态：DRAFT
日期：2026-05-16
作者：AEGIS Steering Committee
依赖：RFC-0001, RFC-0002, RFC-0003, RFC-0004, RFC-0005, RFC-0006

---

## 1. Abstract

定义 AEF 生态中“合规认证 (Compliance Certification)”的等级体系、测试流程和认证徽章规范。合规认证是对 Runtime 实现 AEF 语义准确性的独立验证。此 RFC 建立 L0 到 L4 五级认证，所有等级通过自动化测试判定，不接受人工干预。

## 2. Motivation

声称“AEF 兼容”如果没有独立验证，就是一句空话。合规认证为生态参与者提供信任基础：一个通过 L4 认证的 Runtime 不仅在格式上符合 AEF，其回放、中断处理、工具调用语义也经过了严格测试。

## 3. Certification Levels

| 认证等级 | 对应确定性等级 | 测试套件 |
|---------|--------------|---------|
| AEF Certified L0 | L0 | 事件格式验证 |
| AEF Certified L1 | L1 | 格式 + 事件序列一致性 |
| AEF Certified L2 | L2 | L1 + 工具调用回放匹配 |
| AEF Certified L3 | L3 | L2 + 因果图完整性 |
| AEF Certified L4 | L4 | L3 + 字节级完整性 |

## 4. Test Suites

### 4.1 L0: Event Format Validation

- 所有输出事件通过 AEF Validator（RFC-0001 核心字段 + 对应 RFC 的必需字段）
- 测试用例数：至少 50 个有效事件和 50 个无效事件

### 4.2 L1: Event Sequence Consistency

- 同一会话回放 10 次，`action` 序列完全一致
- 事件数量一致
- 测试用例数：至少 5 个不同的会话场景

### 4.3 L2: Tool Call Replay Match

- 所有 `deterministic = true` 的工具调用在回放中产生相同结果
- 按 RFC-0002 容差规则验证
- 测试用例数：至少 100 个工具调用

### 4.4 L3: Causality Graph Integrity

- 回放产生的因果图与原始图同构
- 所有 `causality_id` 关系一致
- `human.override` 和 `agent.interrupted` 事件按 RFC-0003、RFC-0005 正确处理

### 4.5 L4: Byte-Level Integrity

- 所有事件（排除非确定性字段）逐字节一致
- `integrity_hash` 链完整且全部匹配
- 测试用例数：至少 10 个完整会话

## 5. Certification Process

### 5.1 申请

任何 Runtime 的开发者可通过提交 PR 到 AEF Compliance Suite 仓库来申请认证。PR 需包含：
- Runtime 名称和版本
- 声称的认证等级
- 执行所有对应测试的日志输出

### 5.2 验证

AEF Compliance Working Group 的自动化系统将：
1. 重新运行测试套件
2. 比对日志输出与预期结果
3. 生成通过/失败报告

整个过程无人工评审环节。

### 5.3 认证发布

通过认证后：
- Runtime 被列入 AEF 官方认证列表
- 获得对应等级的认证徽章（可嵌入 README）
- 认证有效期为 12 个月，之后需重新验证

## 6. Certification Badge

认证徽章格式：

```markdown
[![AEF Certified](https://aegis-standard.org/badges/certified-l4.svg)](https://aegis-standard.org/certified)

徽章由 AEGIS 官方生成，包含防篡改哈希，链接指向认证详情页。

7. Revocation
认证在以下情况撤销：

发现 Runtime 行为与声称等级不符（经测试验证）

Runtime 引入安全漏洞影响证据完整性

开发者主动申请撤销

撤销后在认证列表中标注“已撤销”并说明原因。

8. Immutability Clause
此 RFC 中第 3 节定义的认证等级名称和层级关系自冻结之日起永不修改。第 5 节定义的自动化验证原则永不变更。

9. References
RFC-0001: Event Core Schema

RFC-0002: Replay Semantics

RFC-0003: Interrupt Semantics

RFC-0004: Tool Invocation Semantics

RFC-0005: Human Override Semantics

RFC-0006: Determinism Guarantees