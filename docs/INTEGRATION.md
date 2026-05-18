# AEF MCP 插装层接入指南

## 概述
接入 AEF MCP 工具，你的 Agent 将自动产生不可篡改的执行证据。

## 前置条件
- Python 3.10+
- 一个已存在的 Agent 项目

## 安装
将 `mcp/server.py` 复制到你的 Agent 项目中，或直接引用 `aef-core` 仓库。

## 配置
在 Agent 的工具列表中注册以下 MCP 工具：
- `aef_normalize`: 标准化事件
- `aef_validate`: 验证事件

## 使用
在 Agent 执行关键操作（如工具调用、任务完成、人类干预）后，调用 `aef_normalize` 记录事件。

## 验证
调用 `aef_validate` 验证已记录的事件链完整性。

## 完整示例
```python
import json
import sys
sys.path.insert(0, 'path/to/mcp')
from server import aef_normalize, validate_event

# 1. 生成事件
event = aef_normalize(
    action="tool.call.completed",
    actor="agent",
    payload={"tool_name": "search", "input": "query", "output": "result"},
    agent_id="my-agent"
)

# 2. 验证事件
result = validate_event(event)
print(json.dumps(result, indent=2))
```

## 常见问题
**Q: 可以不装 Traccia 吗？**  
A: 可以，AEF MCP 工具独立运行，无需 Traccia。

**Q: 事件存在哪里？**  
A: 事件以 JSON 形式返回，可存储在任何地方（文件、数据库等）。

**Q: 如何自定义 action 类型？**  
A: 参考 `semantic-registry.yaml` 中的定义，或使用标准 action 类型。

**Q: 支持哪些 actor 类型？**  
A: 仅支持 `human` 和 `agent`。

**Q: 如何验证事件链？**  
A: 使用 `aef_chain_verify` 工具验证事件列表的完整性。
