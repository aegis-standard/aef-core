#!/usr/bin/env python3
"""
AEF Instrumentor MCP Server — 提供 AEF 事件标准化、验证和链完整性检查工具。

严格遵守 AEF 宪法：
1. 不做智能，只做观测
2. 仅使用 Python 标准库
3. 代码总量不超过 200 行
"""

import json
import hashlib
import uuid
import datetime
import sys

# AEF RFC-0001 必需字段
REQUIRED_FIELDS = ["id", "timestamp", "session_id", "causality_id", "actor", "agent_id", "action", "payload", "integrity_hash", "metadata"]
VALID_ACTORS = {"human", "agent"}

# 语义注册表映射
ACTION_MAPPING = {
    "search": "tool.call.completed", "run_code": "tool.call.completed", "execute": "tool.call.completed",
    "call": "tool.call.completed", "invoke": "tool.call.completed", "start": "agent.call.started",
    "finish": "agent.call.completed", "complete": "task.completed", "create": "task.created",
    "error": "agent.error", "override": "human.override",
}

VALID_ACTIONS = {
    "task.created", "task.plan.generated", "agent.call.started", "agent.call.completed",
    "tool.call.started", "tool.call.completed", "agent.error", "agent.recovery.attempt",
    "human.intervention", "human.override", "memory.updated", "task.completed"
}


def compute_hash(event):
    """计算事件完整性哈希（排除 integrity_hash 字段）"""
    copy = {k: v for k, v in event.items() if k != "integrity_hash"}
    raw = json.dumps(copy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_event(event):
    """验证单个事件的合法性"""
    details = []
    missing = [f for f in REQUIRED_FIELDS if f not in event]
    if missing:
        details.append(f"缺少字段: {missing}")
    if event.get("actor") not in VALID_ACTORS:
        details.append(f"actor '{event.get('actor')}' 无效")
    action = event.get("action")
    if action not in VALID_ACTIONS:
        details.append(f"action '{action}' 未注册")
    if event.get("actor") == "agent" and not event.get("agent_id"):
        details.append("actor=agent 时 agent_id 不能为空")
    if action == "human.override":
        payload = event.get("payload", {})
        for f in ["original_output", "corrected_output", "override_reason"]:
            if f not in payload:
                details.append(f"human.override 缺少 payload.{f}")
    expected = compute_hash(event)
    actual = event.get("integrity_hash")
    if actual and expected != actual:
        details.append(f"哈希不匹配")
    timestamp = event.get("timestamp")
    if timestamp:
        try:
            datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            details.append(f"timestamp 格式无效")
    return {"valid": len(details) == 0, "message": "VALID" if len(details) == 0 else f"INVALID — {len(details)} 个错误", "details": details}


def normalize_action(action):
    """将不规范的 action 名称映射到标准 AEF action"""
    return action if action in VALID_ACTIONS else ACTION_MAPPING.get(action, "tool.call.completed")


def aef_normalize(action, actor, payload, session_id=None, causality_id=None, agent_id=None):
    """标准化 Agent 调用为 AEF 事件"""
    event_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    normalized_action = normalize_action(action)
    event = {
        "id": event_id, "timestamp": now, "session_id": session_id or str(uuid.uuid4()),
        "causality_id": causality_id, "actor": actor,
        "agent_id": agent_id if actor == "agent" else None,
        "action": normalized_action, "payload": payload, "integrity_hash": None,
        "metadata": {"source": "aef-instrumentor", "schema_version": "1.0", "tags": []}
    }
    event["integrity_hash"] = compute_hash(event)
    return event


def aef_chain_verify(events):
    """验证事件列表的哈希链和因果链完整性"""
    if not events:
        return {"valid": False, "message": "事件列表为空", "details": ["事件列表为空"]}
    details = []
    event_ids = set()
    for event in events:
        if "id" in event:
            event_ids.add(event["id"])
    for i, event in enumerate(events):
        seq = i + 1
        validation = validate_event(event)
        if not validation["valid"]:
            details.append(f"事件 #{seq}: {validation['message']}")
            details.extend([f"  - {d}" for d in validation["details"]])
        causality = event.get("causality_id")
        if i == 0 and causality is not None:
            details.append(f"事件 #{seq}: 首事件的 causality_id 必须为 null")
        elif i > 0 and causality is not None and causality not in event_ids:
            details.append(f"事件 #{seq}: causality_id '{causality}' 不存在")
    for i, event in enumerate(events):
        seq = i + 1
        expected_hash = compute_hash(event)
        actual_hash = event.get("integrity_hash")
        if actual_hash and expected_hash != actual_hash:
            details.append(f"事件 #{seq}: 哈希链断裂")
    return {"valid": len(details) == 0, "message": f"VALID — {len(events)} 个事件" if len(details) == 0 else f"INVALID — {len(details)} 个错误", "details": details}


# MCP 工具定义
TOOLS = {
    "aef_validate": {"description": "验证事件合法性", "input_schema": {"type": "object", "properties": {"event": {"type": "object"}}, "required": ["event"]}},
    "aef_normalize": {"description": "标准化为 AEF 事件", "input_schema": {"type": "object", "properties": {"action": {"type": "string"}, "actor": {"type": "string"}, "payload": {"type": "object"}}, "required": ["action", "actor", "payload"]}},
    "aef_chain_verify": {"description": "验证事件链完整性", "input_schema": {"type": "object", "properties": {"events": {"type": "array", "items": {"type": "object"}}}, "required": ["events"]}}
}


def handle_request(request):
    """处理 MCP 请求"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "aef-instrumentor", "version": "1.0.0"}}}
    elif method == "tools/list":
        tools_list = [{"name": name, "description": tool["description"], "inputSchema": tool["input_schema"]} for name, tool in TOOLS.items()]
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools_list}}
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            if tool_name == "aef_validate":
                result = validate_event(arguments["event"])
            elif tool_name == "aef_normalize":
                result = aef_normalize(action=arguments["action"], actor=arguments["actor"], payload=arguments["payload"], session_id=arguments.get("session_id"), causality_id=arguments.get("causality_id"), agent_id=arguments.get("agent_id"))
            elif tool_name == "aef_chain_verify":
                result = aef_chain_verify(arguments["events"])
            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"未知工具: {tool_name}"}}
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": f"工具执行错误: {str(e)}"}}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"未知方法: {method}"}}


def main():
    """MCP 服务器主循环（基于 stdio 的 JSON-RPC）"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON 解析错误"}}
            print(json.dumps(error_response, ensure_ascii=False))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
