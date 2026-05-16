# AEF-RFC-0001: Event Core Schema

**状态**：FROZEN
**日期**：2026-05-16
**作者**：AEGIS Steering Committee

## Abstract

定义 AEF 事件的核心字段集合及其不可变语义。

## Core Fields

| 字段 | 类型 | 必需 | 语义 |
|------|------|------|------|
| `id` | string (UUID v4) | 是 | 事件全局唯一标识符 |
| `timestamp` | string (ISO 8601) | 是 | 事件发生的物理时间，不可回填 |
| `session_id` | string (UUID v4) | 是 | 一次完整任务会话的唯一标识 |
| `causality_id` | string \| null | 是 | 直接父事件 id，null 表示因果链起点 |
| `actor` | "human" \| "agent" | 是 | 行为主体类型 |
| `agent_id` | string \| null | 否 | 当 actor=agent 时标识具体 Agent |
| `action` | string | 是 | 行为语义类型，必须在 Action Registry 中注册 |
| `payload` | object | 是 | 行为详细数据 |
| `integrity_hash` | string \| null | 否 | SHA-256 事件内容哈希 |
| `metadata` | object | 是 | 包含 source, schema_version, tags |

## Immutability

此 RFC 中所有字段定义自冻结之日起永不修改。
扩展字段通过新 RFC 编号进行。