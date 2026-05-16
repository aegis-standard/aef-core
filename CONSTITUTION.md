# AEGIS Constitution v1.0

**生效日期**：2026-05-16
**状态**：FROZEN

## Preamble

AEGIS (Agent Execution Governance Infrastructure Standard) 是一个开放、中立、永久免费的 AI 代理执行治理基础设施标准。

它的核心是 AEF (Agent Evidence Format)——一份定义“AI 行为什么叫真实发生”的执行证据宪法。

## Foundational Principles

1. **Evidence over Execution** — 标准定义的是行为证据，不是执行方式。
2. **Semantic Immutability** — 已发布的语义定义永不可修改。只能新增版本。
3. **Field Add-Only** — 已发布字段永不删除。扩展通过命名空间进行。
4. **RFC Mandatory** — 任何语义变更必须经过 RFC 流程，包含向后兼容性分析。
5. **Absolute Neutrality** — AEF 不绑定任何 Runtime、厂商、平台。
6. **Evidence Only** — AEF 只定义证据。不接受记忆、人格、工作流等扩展。
7. **Compliance Automated** — 合规认证由算法判定，不接受人工干预。
8. **Local-First** — 所有参考实现必须支持完全本地运行。

## Permanent Assets

以下资产被指定为 AEGIS 永久资产，不可废弃：

- AEF Semantics Registry（事件语义词典）
- AEF Compliance Suite（可执行合规测试向量集）
- AEF Validator（事件格式验证器）
- Claw Reference Runtime（参考实现）

## Governance

AEGIS 由 Steering Committee (ASC) 治理。
RFC 流程：任何人提交草案 → 社区讨论 → 实现验证 → ASC 投票。
合规认证：完全自动化，公开可复现。

## Forbidden Actions

- 在 AEF 中加入记忆、人格、工作流相关语义
- 在 AEF 仓库中推广特定 Runtime
- 修改已发布的事件语义
- 删除已发布的字段
- 对合规认证收费
- 人工判定合规结果

---

此宪法自发布之日起生效。修改需经过 ASC 投票并发布修正案。