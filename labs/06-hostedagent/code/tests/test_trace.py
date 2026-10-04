from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT.parents[1] / "05-foundry-iq/helper/code"))


class TraceTests(unittest.TestCase):
    def test_fabric_answer_is_extracted_and_keeps_its_reference_link(self):
        from trace_view import debug_trace
        answer = "NCR-2026-0001 / 공정검사 / 생산관리팀 / 선별 / 승인"
        result = {
            "activity": [{"id": 1, "type": "fabricDataAgent",
                          "knowledgeSourceName": "ks-quality-fabric-v2", "count": 1}],
            "references": [{"id": "0", "type": "fabricDataAgent", "activitySource": 1,
                            "sourceData": {"fabricAnswer": answer}}],
            "response": [{"content": [{"type": "text", "text": "요약 [ref_id:0]"}]}],
        }
        ref = debug_trace(result)["references"][0]
        self.assertEqual("available", ref["sourceContentStatus"])
        self.assertEqual(answer, ref["sourcePreview"])
        self.assertEqual("sourceData.fabricAnswer", ref["sourceContentField"])
        self.assertEqual("ks-quality-fabric-v2", ref["source"])
        self.assertTrue(ref["cited"])
        self.assertEqual({"fabricAnswer": answer}, result["references"][0]["sourceData"])

    def test_encoded_fabric_answer_keeps_length_limit_and_redaction(self):
        import json
        from trace_view import debug_trace, SOURCE_CONTENT_LIMIT
        source = json.dumps({"fabricAnswer": {
            "api_key": "do-not-leak",
            "records": "NCR 근거\n" * SOURCE_CONTENT_LIMIT,
        }}, ensure_ascii=False)
        ref = debug_trace({"references": [
            {"id": "0", "type": "fabricDataAgent", "sourceData": source},
        ]})["references"][0]
        self.assertEqual("available", ref["sourceContentStatus"])
        self.assertEqual("sourceData.fabricAnswer", ref["sourceContentField"])
        self.assertEqual("json", ref["sourceContentFormat"])
        self.assertEqual(SOURCE_CONTENT_LIMIT, len(ref["sourcePreview"]))
        self.assertGreater(ref["sourceContentLength"], SOURCE_CONTENT_LIMIT)
        self.assertTrue(ref["previewTruncated"])
        self.assertNotIn("do-not-leak", ref["sourcePreview"])

    def test_search_snippet_is_extracted_before_metadata_and_preview_limit(self):
        from trace_view import debug_trace
        snippet = "실제 장비 점검 절차입니다.\n" * 100
        trace = debug_trace({"references": [{"id": "0", "type": "azureBlob", "sourceData": {
            "uid": "guid-" * 80, "blob_url": "https://example.com/" + "p" * 300, "snippet": snippet,
        }}]})
        ref = trace["references"][0]
        self.assertEqual(snippet, ref["sourcePreview"])
        self.assertEqual("sourceData.snippet", ref["sourceContentField"])
        self.assertEqual("available", ref["sourceContentStatus"])
        self.assertFalse(ref["previewTruncated"])
        self.assertEqual(len(snippet), ref["sourceContentLength"])
        self.assertNotIn("guid-", ref["sourcePreview"])
        self.assertIn("uid", ref["sourceMetadata"])

    def test_search_chunk_and_encoded_content_preserve_the_actual_passage(self):
        from trace_view import debug_trace
        import json
        data = [{"chunk_id": "metadata", "chunk": "작업지시 본문"},
                json.dumps({"uid": "metadata", "content": "매뉴얼 본문"}, ensure_ascii=False)]
        for source, text in zip(data, ["작업지시 본문", "매뉴얼 본문"]):
            with self.subTest(source=source):
                ref = debug_trace({"references": [{"id": "1", "sourceData": source}]})["references"][0]
                self.assertEqual(text, ref["sourcePreview"])

    def test_text_parts_are_combined_but_metadata_only_is_not_shown_as_content(self):
        from trace_view import debug_trace
        refs = debug_trace({"references": [
            {"id": "1", "sourceData": {"parts": [{"text": "첫 근거"}, {"text": "다음 근거"}]}},
            {"id": "2", "sourceData": {"uid": "only-guid", "blob_url": "https://example.com"}},
            {"id": "3"},
        ]})["references"]
        self.assertEqual("첫 근거\n\n다음 근거", refs[0]["sourcePreview"])
        self.assertEqual("unavailable", refs[1]["sourceContentStatus"])
        self.assertNotIn("sourcePreview", refs[1])
        self.assertEqual("missing", refs[2]["sourceContentStatus"])

    def test_structured_tool_content_is_redacted_after_decoding(self):
        from trace_view import debug_trace
        import json
        source = {"title": "tool", "content": json.dumps({
            "lot_id": "LOT0012", "status": "Running", "api_key": "do-not-leak",
        })}
        ref = debug_trace({"references": [{"id": "1", "sourceData": source}]})["references"][0]
        self.assertEqual("json", ref["sourceContentFormat"])
        self.assertIn("LOT0012", ref["sourcePreview"])
        self.assertNotIn("do-not-leak", ref["sourcePreview"])

    def test_planning_passes_are_not_claimed_as_search_retries(self):
        from trace_view import debug_trace
        result = {"activity": [
            {"id": 0, "type": "modelQueryPlanning", "inputTokens": 10},
            {"id": 1, "type": "searchIndex", "knowledgeSourceName": "source", "count": 0,
             "searchIndexArguments": {"search": "first"}},
            {"id": 2, "type": "modelQueryPlanning"},
            {"id": 3, "type": "searchIndex", "knowledgeSourceName": "source", "count": 2,
             "searchIndexArguments": {"search": "second"}},
            {"id": 4, "type": "modelAnswerSynthesis"},
        ], "references": [{"id": "0", "activitySource": 3}],
            "response": [{"content": [{"type": "text", "text": "답변 [ref_id:0]"}]}]}
        trace = debug_trace(result)
        self.assertEqual(2, trace["metrics"]["planning_passes"])
        self.assertEqual(2, trace["metrics"]["search_calls"])
        self.assertEqual(1, trace["metrics"]["additional_source_calls"])
        self.assertEqual(1, trace["metrics"]["synthesis_passes"])
        self.assertEqual("second", trace["queries"][1]["arguments"]["searchIndexArguments"]["search"])
        self.assertEqual("source", trace["references"][0]["source"])
        self.assertTrue(trace["references"][0]["cited"])

    def test_empty_trace_is_unknown_not_fabricated_work(self):
        from trace_view import debug_trace
        trace = debug_trace({})
        self.assertFalse(trace["available"])
        self.assertEqual(0, trace["metrics"]["search_calls"])

    def test_secrets_and_unbounded_source_content_are_not_exposed(self):
        from trace_view import debug_trace, SOURCE_CONTENT_LIMIT
        trace = debug_trace({"activity": [
            {"id": 1, "type": "mcpServer", "knowledgeSourceName": "source", "count": 1,
             "mcpServerArguments": {"headers": {"x-ms-query-source-authorization": "secret-token",
                                               "x-client-search-authorization": "secret-token"}},
             "error": "Bearer eyJ-secret-value"},
        ], "references": [{"id": "0", "activitySource": 1,
                          "sourceData": {"text": "x" * (SOURCE_CONTENT_LIMIT + 500)}}]})
        import json
        serialized = json.dumps(trace)
        self.assertNotIn("secret-token", serialized)
        self.assertNotIn("eyJ-secret-value", serialized)
        self.assertEqual(SOURCE_CONTENT_LIMIT, len(trace["references"][0]["sourcePreview"]))
        self.assertTrue(trace["references"][0]["previewTruncated"])
        self.assertNotIn("x" * (SOURCE_CONTENT_LIMIT + 1), serialized)


if __name__ == "__main__":
    unittest.main()
