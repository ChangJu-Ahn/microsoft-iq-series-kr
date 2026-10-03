import importlib.util
from pathlib import Path
import unittest


class RetrievalTraceTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name("retrieval_trace.py")
        self.assertTrue(path.exists(), "응답 로그 파서가 필요합니다.")
        spec = importlib.util.spec_from_file_location("retrieval_trace", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_queries_references_and_citations_join_by_id_not_position(self):
        result = {
            "activity": [
                {"id": 8, "type": "modelQueryPlanning", "inputTokens": 50},
                {"id": 42, "type": "searchIndex", "knowledgeSourceName": "docs",
                 "count": 3, "searchIndexArguments": {"search": "CMP", "filter": "kind eq 'manual'"}},
            ],
            "references": [{"id": "7", "activitySource": 42, "rerankerScore": 2.5,
                            "sourceData": {"title": "manual", "chunk": "pressure"}}],
            "response": [{"content": [{"type": "text", "text": "기준 [ref_id:7]"}]}],
        }
        trace = self.module.parse_trace(result)
        self.assertEqual(trace["queries"][0]["arguments"]["searchIndexArguments"]["search"], "CMP")
        self.assertEqual(trace["references"][0]["source"], "docs")
        self.assertTrue(trace["references"][0]["cited"])
        self.assertEqual(trace["references"][0]["sourceData"]["chunk"], "pressure")
        self.assertEqual(trace["timeline"][0]["details"]["inputTokens"], 50)

    def test_planning_twice_does_not_invent_retrieval(self):
        trace = self.module.parse_trace({"activity": [
            {"id": 0, "type": "modelQueryPlanning"},
            {"id": 1, "type": "workIQ", "knowledgeSourceName": "work", "count": 1},
            {"id": 2, "type": "modelQueryPlanning"},
        ]})
        self.assertEqual(trace["repeatedQueries"], [])
        self.assertEqual(len(trace["queries"]), 1)

    def test_repeated_source_does_not_invent_reason(self):
        trace = self.module.parse_trace({"activity": [
            {"id": 2, "type": "mcpServer", "knowledgeSourceName": "mes", "count": 0,
             "mcpServerArguments": {"toolName": "route", "toolArguments": {"stage": "CMP"}}},
            {"id": 3, "type": "modelQueryPlanning"},
            {"id": 4, "type": "mcpServer", "knowledgeSourceName": "mes", "count": 1,
             "mcpServerArguments": {"toolName": "route", "toolArguments": {"step_code": "CMP"}}},
        ]})
        repeat = trace["repeatedQueries"][0]
        self.assertEqual((repeat["previousId"], repeat["id"]), (2, 4))
        self.assertTrue(repeat["argumentsChanged"])
        self.assertIn("명시되지", repeat["reason"])

    def test_parallel_calls_and_missing_duration_are_not_serialized(self):
        trace = self.module.parse_trace({"activity": [
            {"id": 2, "type": "searchIndex", "knowledgeSourceName": "b",
             "startedAt": "2026-10-01T00:00:02Z", "completedAt": "2026-10-01T00:00:04Z"},
            {"id": 1, "type": "searchIndex", "knowledgeSourceName": "a",
             "startedAt": "2026-10-01T00:00:01Z", "completedAt": "2026-10-01T00:00:03Z"},
        ]})
        self.assertEqual([r["id"] for r in trace["timeline"]], [1, 2])
        self.assertEqual(trace["timeline"][0]["durationMs"], 2000)
        self.assertEqual(trace["overlaps"], [[1, 2]])
        missing = self.module.parse_trace({"activity": [{"id": 0, "type": "agenticReasoning"}]})
        self.assertIsNone(missing["timeline"][0]["durationMs"])

    def test_errors_warnings_and_unknown_types_remain_visible(self):
        result = {"activity": [{"id": 1, "type": "futureActivity",
                               "error": {"message": "timeout"}, "warning": "truncated"}]}
        trace = self.module.parse_trace(result)
        self.assertEqual(trace["timeline"][0]["details"]["error"]["message"], "timeout")
        self.assertEqual(trace["timeline"][0]["details"]["warning"], "truncated")
        self.assertEqual(trace["timeline"][0]["type"], "futureActivity")
        self.assertIn("미제공", self.module.format_trace(self.module.parse_trace({})))

    def test_overlap_requires_shared_time_not_touching_intervals_or_elapsed_ms(self):
        trace = self.module.parse_trace({"activity": [
            {"id": 1, "type": "mcpServer", "knowledgeSourceName": "mes",
             "startedAt": "2026-10-01T00:00:01Z", "completedAt": "2026-10-01T00:00:03Z"},
            {"id": 2, "type": "azureBlob", "knowledgeSourceName": "manual", "elapsedMs": 0,
             "startedAt": "2026-10-01T00:00:02Z", "completedAt": "2026-10-01T00:00:03Z"},
            {"id": 3, "type": "mcpServer", "knowledgeSourceName": "mes",
             "startedAt": "2026-10-01T00:00:03Z", "completedAt": "2026-10-01T00:00:04Z"},
            {"id": 4, "type": "mcpServer", "knowledgeSourceName": "web", "elapsedMs": 100},
        ]})
        self.assertEqual(trace["overlaps"], [[1, 2]])

    def test_missing_reference_targets_and_unused_references(self):
        trace = self.module.parse_trace({
            "references": [{"id": "1", "activitySource": 99}],
            "response": [{"content": [{"type": "text", "text": "[ref_id:2]"}]}],
        })
        self.assertIsNone(trace["references"][0]["source"])
        self.assertFalse(trace["references"][0]["cited"])
        self.assertEqual(trace["unresolvedCitations"], ["2"])

    def test_redacts_credentials_but_preserves_token_metrics(self):
        trace = self.module.parse_trace({"activity": [
            {"id": 0, "type": "mcpServer", "knowledgeSourceName": "web",
             "inputTokens": 42, "mcpServerArguments": {
                 "headers": {"x-apikey": "secret", "Authorization": "Bearer secret"},
                 "toolArguments": {"query": "CMP"}}},
        ]})
        rendered = self.module.format_trace(trace)
        self.assertNotIn("secret", rendered)
        self.assertIn("42", rendered)
        self.assertIn("CMP", rendered)


if __name__ == "__main__":
    unittest.main()
