#!/usr/bin/env python3
"""
AEF Instrumentor 测试 — 使用 unittest 验证核心功能
"""

import unittest
import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from server import aef_normalize, validate_event, aef_chain_verify, compute_hash


class TestAEFInstrumentor(unittest.TestCase):
    """测试 AEF Instrumentor 的三个核心工具"""

    def test_aef_normalize_completes_missing_fields(self):
        """测试 aef_normalize 能正确补全缺失字段并计算哈希"""
        # 输入最小参数
        event = aef_normalize(
            action="search",
            actor="agent",
            payload={"query": "test"},
            agent_id="test-agent-1"
        )

        # 验证所有必需字段都存在
        required_fields = [
            "id", "timestamp", "session_id", "causality_id",
            "actor", "agent_id", "action", "payload",
            "integrity_hash", "metadata"
        ]
        for field in required_fields:
            self.assertIn(field, event, f"缺少字段: {field}")

        # 验证 action 映射正确
        self.assertEqual(event["action"], "tool.call.completed")

        # 验证 actor 和 agent_id
        self.assertEqual(event["actor"], "agent")
        self.assertEqual(event["agent_id"], "test-agent-1")

        # 验证哈希计算正确
        expected_hash = compute_hash(event)
        self.assertEqual(event["integrity_hash"], expected_hash)

        # 验证 metadata 结构
        self.assertIn("source", event["metadata"])
        self.assertIn("schema_version", event["metadata"])
        self.assertIn("tags", event["metadata"])

    def test_aef_validate_detects_tampered_payload(self):
        """测试 aef_validate 能检测出篡改过 payload 的事件"""
        # 创建一个有效事件
        original_event = aef_normalize(
            action="run_code",
            actor="agent",
            payload={"code": "print('hello')"},
            agent_id="test-agent-2"
        )

        # 篡改 payload
        tampered_event = original_event.copy()
        tampered_event["payload"] = {"code": "print('malicious')"}

        # 验证原始事件应该通过
        original_result = validate_event(original_event)
        self.assertTrue(original_result["valid"], "原始事件应该有效")

        # 验证篡改事件应该失败（哈希不匹配）
        tampered_result = validate_event(tampered_event)
        self.assertFalse(tampered_result["valid"], "篡改事件应该无效")
        self.assertTrue(any("哈希不匹配" in detail for detail in tampered_result["details"]),
                        "应该检测到哈希不匹配")

    def test_aef_chain_verify_detects_broken_causality(self):
        """测试 aef_chain_verify 能检测出断裂的因果链"""
        # 创建三个事件，形成因果链
        event1 = aef_normalize(
            action="create",
            actor="human",
            payload={"task": "test task"}
        )

        event2 = aef_normalize(
            action="start",
            actor="agent",
            payload={"step": 1},
            causality_id=event1["id"],
            agent_id="agent-1"
        )

        event3 = aef_normalize(
            action="finish",
            actor="agent",
            payload={"result": "done"},
            causality_id=event2["id"],
            agent_id="agent-1"
        )

        # 正常链应该通过验证
        valid_chain = [event1, event2, event3]
        result = aef_chain_verify(valid_chain)
        self.assertTrue(result["valid"], "正常因果链应该有效")

        # 创建断裂的因果链（event3 指向不存在的事件）
        broken_event3 = event3.copy()
        broken_event3["causality_id"] = "non-existent-id"

        broken_chain = [event1, event2, broken_event3]
        broken_result = aef_chain_verify(broken_chain)
        self.assertFalse(broken_result["valid"], "断裂的因果链应该无效")
        self.assertTrue(any("causality_id" in detail and "不存在" in detail 
                           for detail in broken_result["details"]),
                        "应该检测到因果链断裂")

    def test_aef_normalize_maps_various_actions(self):
        """测试 action 映射功能"""
        test_cases = [
            ("search", "tool.call.completed"),
            ("run_code", "tool.call.completed"),
            ("execute", "tool.call.completed"),
            ("start", "agent.call.started"),
            ("finish", "agent.call.completed"),
            ("complete", "task.completed"),
            ("create", "task.created"),
            ("error", "agent.error"),
            ("override", "human.override"),
            # 已经是标准 action 的应该保持不变
            ("tool.call.completed", "tool.call.completed"),
            ("task.created", "task.created"),
        ]

        for input_action, expected_action in test_cases:
            event = aef_normalize(
                action=input_action,
                actor="agent",
                payload={"test": True},
                agent_id="test-agent"
            )
            self.assertEqual(event["action"], expected_action,
                             f"Action '{input_action}' 应该映射为 '{expected_action}'")

    def test_aef_validate_checks_required_fields(self):
        """测试必需字段检查"""
        # 创建缺少字段的事件
        incomplete_event = {
            "id": "test-id",
            "timestamp": "2026-05-17T12:00:00Z",
            # 缺少 session_id, causality_id, actor, agent_id, action, payload, integrity_hash, metadata
        }

        result = validate_event(incomplete_event)
        self.assertFalse(result["valid"], "缺少字段的事件应该无效")
        self.assertTrue(len(result["details"]) > 0, "应该有错误详情")

    def test_aef_chain_verify_empty_list(self):
        """测试空事件列表"""
        result = aef_chain_verify([])
        self.assertFalse(result["valid"], "空列表应该无效")
        self.assertEqual(result["message"], "事件列表为空")


if __name__ == "__main__":
    unittest.main(verbosity=2)
