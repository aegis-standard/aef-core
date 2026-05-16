# AEF-RFC-0004: Tool Invocation Semantics

状态：DRAFT
日期：2026-05-16
作者：AEGIS Steering Committee
依赖：RFC-0001 (Event Core Schema)
关联：RFC-0002 (Replay Semantics), RFC-0006 (Determinism Guarantees)

---

## 1. Abstract

定义 AEF 生态中“工具调用 (Tool Invocation)”的精确语义。包括工具调用的启动、完成、失败三种事件类型，工具注册表格式，错误处理规范，以及版本兼容性约定。此 RFC 是 AEF Tool Extension 的基础。

## 2. Motivation

工具调用是 Agent 与外部世界交互的唯一渠道。如果工具调用的语义不统一，不同 Runtime 产生的证据将无法互认。此 RFC 的目标是提供一份可跨 Runtime 通用的工具调用证据标准。

## 3. Tool Call Event Types

### 3.1 事件类型

| action | 含义 |
|--------|------|
| `tool.call.started` | 工具调用开始执行 |
| `tool.call.completed` | 工具调用成功完成 |
| `tool.call.error` | 工具调用失败 |

### 3.2 必需字段

- `tool.call.started` 的 `payload` 必须包含：
  - `tool_name`: string — 工具名称（必须在 AEF Tool Registry 中注册）
  - `input`: object — 工具入参
- `tool.call.completed` 的 `payload` 必须包含：
  - `tool_name`: string
  - `output`: any — 工具出参。如果工具被标记为 `deterministic = true`，output 必须附带完整性哈希
- `tool.call.error` 的 `payload` 必须包含：
  - `tool_name`: string
  - `error`: string — 错误描述（人类可读）

## 4. Tool Registry

### 4.1 注册表格式

任何被 AEF 兼容 Runtime 调用的工具，必须在 AEF Tool Registry 中注册。注册表格式如下：

```yaml
tools:
  - name: string              # 工具唯一标识
    version: string           # 语义版本
    description: string       # 工具功能描述
    deterministic: boolean    # 是否确定性工具
    input_schema: object      # JSON Schema 格式的入参定义
    output_schema: object     # JSON Schema 格式的出参定义
    rfc: string               # 关联的 RFC 编号

    4.2 确定性标记
deterministic = true：工具对于相同输入总是产生相同输出。此类工具的 tool.call.completed 事件参与回放匹配。

deterministic = false：工具输出可能因外部状态而变化（如 API 调用、当前时间）。此类工具的 output 不参与确定性回放匹配。

4.3 注册表维护
AEF Tool Registry 随 RFC 更新。新增工具类型通过新 RFC 编号注册。

5. Error Handling
5.1 错误不中断会话
tool.call.error 表示工具调用失败，但会话本身不终止。Agent 可基于错误信息决定重试、使用替代工具或请求人类干预。

5.2 错误事件的位置
tool.call.error 在因果链中的位置与 tool.call.completed 完全相同——它的 causality_id 指向对应的 tool.call.started，说明错误发生在该工具调用期间。

5.3 超时
工具调用超时视为一种错误，产生 tool.call.error，error 字段注明 timeout 及超时时间。

6. Version Compatibility
6.1 工具版本
工具版本遵循语义版本规范 (SemVer)。规则：

主版本号 (Major)：输入或输出 Schema 不兼容变更

次版本号 (Minor)：新增可选字段，向后兼容

修订号 (Patch)：工具实现修正，不影响 Schema

6.2 回放兼容性
回放时，Runtime 必须记录调用工具时的实际 tool_name 和 version。如果回放 Runtime 中该工具版本不同，必须标记 tool_version_mismatch: true，但回放本身不判定为 INVALID（由审计者自行判断）。

7. Immutability Clause
此 RFC 中第 3 节定义的工具调用事件类型、第 5 节定义的错误处理规范自冻结之日起永不修改。第 4 节定义的注册表格式可扩展字段（通过新 RFC），但不得删除已有字段。

8. References
RFC-0001: Event Core Schema

RFC-0002: Replay Semantics

RFC-0006: Determinism Guarantees (DRAFT)