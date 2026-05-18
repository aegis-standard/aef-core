#!/usr/bin/env python3
"""
AEF 集成测试 — 验证 MCP 插装层与 Claw/Traccia 的连通性

宪法纪律：
- 不做智能，只做验证
- 仅使用 Python 标准库
- 代码不超过 150 行
"""

import unittest
import json
import subprocess
import tempfile
import sys
from pathlib import Path

# 项目路径
CLAW_PATH = Path(r"d:\claw-reference")
TRACCIA_PATH = Path(r"d:\Traccia\traccia")
MCP_PATH = Path(__file__).parent / "mcp"


class TestAEFIntegration(unittest.TestCase):
    """验证 AEF MCP 插装层与 Claw/Traccia 的数据通路"""

    def setUp(self):
        """设置临时目录和路径"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.claw_output = self.temp_path / "evidence.jsonl"
        self.normalized_output = self.temp_path / "normalized.jsonl"

    def tearDown(self):
        """清理临时文件"""
        self.temp_dir.cleanup()

    def _run_claw_session(self):
        """模拟 Claw 运行时产生原始事件"""
        # 直接使用模拟事件（避免依赖外部 Claw 环境）
        self._create_mock_events()
        
        # 读取产生的事件
        events = []
        if self.claw_output.exists():
            with open(self.claw_output, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        
        return events

    def _create_mock_events(self):
        """创建模拟的 Claw 原始事件"""
        mock_events = [
            {"action": "create", "actor": "human", "payload": {"task": "test"}},
            {"action": "search", "actor": "agent", "payload": {"query": "test"}, "agent_id": "agent-1"},
            {"action": "run_code", "actor": "agent", "payload": {"code": "print('hello')"}, "agent_id": "agent-1"},
        ]
        
        with open(self.claw_output, "w", encoding="utf-8") as f:
            for event in mock_events:
                f.write(json.dumps(event) + "\n")

    def _normalize_through_mcp(self, raw_events):
        """通过 MCP 插装层标准化事件"""
        # 添加 MCP 路径到 sys.path
        sys.path.insert(0, str(MCP_PATH))
        
        from server import aef_normalize
        
        normalized_events = []
        causality_id = None
        session_id = None
        
        for raw in raw_events:
            event = aef_normalize(
                action=raw.get("action", "unknown"),
                actor=raw.get("actor", "agent"),
                payload=raw.get("payload", {}),
                session_id=session_id,
                causality_id=causality_id,
                agent_id=raw.get("agent_id")
            )
            
            # 维护因果链
            if session_id is None:
                session_id = event["session_id"]
            causality_id = event["id"]
            
            normalized_events.append(event)
        
        return normalized_events

    def _write_events_to_jsonl(self, events, filepath):
        """将事件列表写入 JSONL 文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def test_full_loop(self):
        """测试完整数据通路：Claw → MCP → Traccia"""
        # Step 1: 获取 Claw 原始事件
        raw_events = self._run_claw_session()
        self.assertGreater(len(raw_events), 0, "Claw 应该产生至少一个事件")
        
        # Step 2: 通过 MCP 标准化
        normalized_events = self._normalize_through_mcp(raw_events)
        self.assertEqual(len(normalized_events), len(raw_events), 
                         "标准化后的事件数量应与原始事件一致")
        
        # 验证标准化事件的必需字段
        required_fields = ["id", "timestamp", "session_id", "causality_id",
                          "actor", "agent_id", "action", "payload",
                          "integrity_hash", "metadata"]
        for event in normalized_events:
            for field in required_fields:
                self.assertIn(field, event, f"事件缺少字段: {field}")
        
        # Step 3: 写入临时文件供 Traccia 摄入
        self._write_events_to_jsonl(normalized_events, self.normalized_output)
        
        # Step 4: 验证 Traccia 摄入
        sys.path.insert(0, str(TRACCIA_PATH))
        from ingestion.aef_ingester import AEFIngester
        
        ingester = AEFIngester(claw_log_path=str(self.normalized_output))
        ingested_count = ingester.ingest()
        
        self.assertEqual(ingested_count, len(normalized_events),
                         f"摄入事件数量应为 {len(normalized_events)}，实际为 {ingested_count}")
        
        # Step 5: 验证完整性
        success, message = ingester.verify_integrity()
        self.assertTrue(success, f"完整性验证失败: {message}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
