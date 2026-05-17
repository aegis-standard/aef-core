#!/usr/bin/env python3
"""
AEF Validator CLI — 验证 AEF 事件追踪文件的合法性

用法:
  python validator/aef-validate.py <trace.json>

输出:
  VALID 或 INVALID，并给出详细校验结果。
"""

import json
import hashlib
import sys
from pathlib import Path

# AEF RFC-0001 必需字段
REQUIRED_FIELDS = [
    "id", "timestamp", "session_id", "causality_id",
    "actor", "agent_id", "action", "payload",
    "integrity_hash", "metadata"
]

VALID_ACTORS = {"human", "agent"}
VALID_ACTIONS = {
    "task.created", "task.completed",
    "tool.call.started", "tool.call.completed", "tool.call.error",
    "human.override",
    "agent.interrupted", "agent.interrupt.resolved",
    "agent.error"
}


def compute_hash(event):
    """计算事件完整性哈希（排除 integrity_hash 字段）"""
    copy = {k: v for k, v in event.items() if k != "integrity_hash"}
    raw = json.dumps(copy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_trace(filepath):
    """验证 AEF 追踪文件，返回 (valid, message, details)"""
    path = Path(filepath)
    if not path.exists():
        return False, f"文件不存在: {filepath}", []

    try:
        trace = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"JSON 解析错误: {e}", []

    events = trace.get("events", [])
    if not isinstance(events, list) or len(events) == 0:
        return False, "未找到事件列表或列表为空", []

    details = []
    event_ids = set()

    for i, event in enumerate(events):
        seq = i + 1

        # 1. 必需字段检查
        missing = [f for f in REQUIRED_FIELDS if f not in event]
        if missing:
            details.append(f"事件 #{seq} ({event.get('id', '?')}): 缺少字段 {missing}")
            continue

        # 2. actor 值域
        if event["actor"] not in VALID_ACTORS:
            details.append(f"事件 #{seq} ({event['id']}): actor '{event['actor']}' 无效")

        # 3. action 注册表检查
        if event["action"] not in VALID_ACTIONS:
            details.append(f"事件 #{seq} ({event['id']}): action '{event['action']}' 未注册")

        # 4. actor/agent_id 逻辑
        if event["actor"] == "agent" and not event.get("agent_id"):
            details.append(f"事件 #{seq} ({event['id']}): actor=agent 但 agent_id 为空")

        # 5. human.override 必需字段
        if event["action"] == "human.override":
            for f in ["original_output", "corrected_output", "override_reason"]:
                if f not in event.get("payload", {}):
                    details.append(f"事件 #{seq} ({event['id']}): human.override 缺少 payload.{f}")

        # 6. 哈希验证
        expected = compute_hash(event)
        actual = event.get("integrity_hash")
        if actual and expected != actual:
            details.append(f"事件 #{seq} ({event['id']}): 哈希不匹配")

        # 7. 事件 ID 唯一性
        eid = event.get("id")
        if eid in event_ids:
            details.append(f"事件 #{seq} ({eid}): 事件 ID 重复")
        event_ids.add(eid)

    # 8. 因果链验证
    for i, event in enumerate(events):
        seq = i + 1
        causality = event.get("causality_id")
        if i == 0 and causality is not None:
            details.append(f"事件 #{seq} ({event['id']}): 首事件的 causality_id 必须为 null")
        elif i > 0 and causality is not None and causality not in event_ids:
            details.append(f"事件 #{seq} ({event['id']}): causality_id '{causality}' 在事件列表中不存在")

    valid = len(details) == 0
    if valid:
        return True, f"VALID — {len(events)} 个事件，全部通过验证", details
    else:
        return False, f"INVALID — {len(details)} 个错误", details


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python validator/aef-validate.py <trace.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    valid, msg, details = validate_trace(filepath)

    if valid:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")
        for d in details:
            print(f"  • {d}")

    sys.exit(0 if valid else 1)