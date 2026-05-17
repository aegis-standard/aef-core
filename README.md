# AEF — Agent Evidence Format

**AI 代理执行证据格式宪法。开放、中立、已冻结。**

---

## 一句话定义

AEF 定义了 **"AI 行为什么叫真实发生"**。它不是框架、不是平台、不是 Agent——它是所有 AI 系统共同遵循的行为证据标准。

---

## 为什么需要 AEF

| 问题 | AEF 的答案 |
|------|-----------|
| AI 做了什么？ | 不可变事件链 |
| 能回放吗？ | 确定性回放验证 |
| 谁修改了输出？ | human.override 事件 |
| 能证明吗？ | 密码学完整性哈希 |
| 责任归谁？ | ERC/JMTD 公证收据 |

---

## 核心原则

1. **Evidence over Execution** — 标准定义的是行为证据，不是执行方式
2. **Semantic Immutability** — 已发布的语义定义永不可修改
3. **Field Add-Only** — 已发布字段永不删除
4. **RFC Mandatory** — 任何语义变更必须经过 RFC 流程
5. **Absolute Neutrality** — 不绑定任何 Runtime、厂商、平台
6. **Evidence Only** — 只定义证据，不接受记忆/人格/工作流扩展
7. **Compliance Automated** — 合规认证由算法判定
8. **Local-First** — 所有参考实现支持完全本地运行

详见 [CONSTITUTION.md](CONSTITUTION.md)

---

## 快速接入（三种模式）

### 模式 A：Hooks Adapter（最低侵入）
```bash
/hooks add pre-tool python aef-producer.py tool {tool_name}


模式 B：Sidecar Gateway（旁路记录）

Agent Runtime → Observable Gateway → AEF Events → Traccia

模式 C：Native Runtime（原生实现）

from event_bus import EventBus
bus.emit(action="tool.call.completed", payload={...})

Runtime 直接产生符合 AEF Core Schema 的事件。

事件核心字段 (RFC-0001)
字段	类型	说明
id	UUID v4	事件全局唯一标识
timestamp	ISO 8601	事件发生时间
session_id	UUID v4	任务会话标识
causality_id	UUID/null	因果链：上一条事件 id
actor	"human"/"agent"	行为主体
action	string	行为语义类型（在 Semantic Registry 注册）
payload	object	行为详细数据
integrity_hash	SHA-256	事件内容哈希
metadata	object	source, schema_version, tags
RFC 目录
RFC	标题	状态
RFC-0001	Event Core Schema	DRAFT
RFC-0002	Replay Semantics	DRAFT
RFC-0003	Interrupt Semantics	DRAFT
RFC-0004	Tool Invocation Semantics	DRAFT
RFC-0005	Human Override Semantics	DRAFT
RFC-0006	Determinism Guarantees	DRAFT
RFC-0007	Compliance Levels	DRAFT
合规认证等级
等级	名称	要求
L0	无保证	事件格式正确
L1	事件结构确定	action 序列一致
L2	工具调用确定	确定性工具输入输出匹配
L3	因果链确定	因果图同构
L4	字节级确定	逐事件哈希一致
参考实现
项目	定位	仓库
Claw	AEF Reference Runtime（执行黑匣子）	claw-reference
Traccia	认知时间线 + 记忆蒸馏	raccia
ERC	责任收据引擎	erc
许可证
AEF 标准本身采用 CC0 1.0 Universal 进入公共领域。

治理
AEF 由 Steering Committee (ASC) 治理。RFC 流程：提交草案 → 社区讨论 → 实现验证 → ASC 投票。详见 CONTRIBUTING.md


