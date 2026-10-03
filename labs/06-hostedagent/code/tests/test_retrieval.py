import json
from pathlib import Path
import sys
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class RetrievalTests(unittest.TestCase):
    def test_notebook_extraction_keeps_all_questions_for_the_same_kb(self):
        from questions import load_questions
        notebook = {"cells": [
            {"cell_type": "code", "source": [
                "first = '공정 질문 A'\n",
                "first_result = retrieve_v2_trace(PROCESS_KB_NAME, first)\n",
                "second = '공정 질문 B'\n",
                "second_result = retrieve_v2_trace(PROCESS_KB_NAME, second)\n",
                "third = '품질 질문'\n",
                "third_result = retrieve_v2_trace(QUALITY_KB_NAME, third)\n",
            ]}
        ]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "questions.ipynb"
            path.write_text(json.dumps(notebook))
            self.assertEqual([
                {"kb": "process", "question": "공정 질문 A"},
                {"kb": "process", "question": "공정 질문 B"},
                {"kb": "quality", "question": "품질 질문"},
            ], load_questions(path))

    def test_reasoning_effort_defaults_to_existing_medium_and_can_select_low(self):
        from agent.retrieval import make_request
        self.assertEqual({"kind": "medium"}, make_request("process", "q", "s", "")[1]["retrievalReasoningEffort"])
        for level in ("low", "medium"):
            with self.subTest(level=level):
                body = make_request("quality", "q", "s", "w", reasoning_effort=level)[1]
                self.assertEqual({"kind": level}, body["retrievalReasoningEffort"])
                self.assertEqual(4, len(body["knowledgeSourceParams"]))

    def test_invalid_reasoning_effort_is_rejected_not_silently_defaulted(self):
        from agent.retrieval import make_request
        for level in ("high", "minimal", "", "Low", None):
            with self.subTest(level=level), self.assertRaises(ValueError):
                make_request("process", "q", "s", "", reasoning_effort=level)

    def test_notebook_questions_are_extracted_without_execution(self):
        from questions import load_questions
        questions = load_questions()
        self.assertEqual({"process", "quality"}, {q["kb"] for q in questions})
        self.assertIn("MES에서 LOT0012 로트 상태를 확인하고", questions[0]["question"])
        self.assertIn("바로 직전 공정의 설비", questions[0]["question"])
        quality = next(q for q in questions if q["kb"] == "quality")
        self.assertIn("NCR-2026-0009", quality["question"])

    def test_quality_request_has_all_sources_and_delegated_headers(self):
        from agent.retrieval import make_request
        path, body, headers = make_request("quality", "질문", "search-token", "work-token")
        self.assertIn("quality-investigation-kb-v2", path)
        self.assertEqual(4, len(body["knowledgeSourceParams"]))
        self.assertEqual("search-token", headers["x-ms-query-source-authorization"])
        self.assertEqual("work-token", headers["x-ms-query-work-iq-source-authorization"])
        self.assertNotIn("token", json.dumps(body))

    def test_quality_requires_workiq_token(self):
        from agent.retrieval import make_request
        with self.assertRaises(ValueError):
            make_request("quality", "질문", "search-token", "")

    def test_unknown_kb_is_rejected(self):
        from agent.retrieval import make_request
        with self.assertRaises(ValueError):
            make_request("../arbitrary", "질문", "search-token", "")

    def test_partial_http_is_not_success_even_with_references(self):
        from agent.retrieval import assess
        result = {"response": [{"content": [{"type": "text", "text": "답변 [ref_id:0]"}]}],
                  "activity": [{"id": 1, "knowledgeSourceName": "ks-process-mes-v2", "count": 1}],
                  "references": [{"id": "0", "activitySource": 1}]}
        report = assess("process", result, 206)
        self.assertFalse(report["passed"])
        self.assertEqual(1, report["sources"][0]["references"])
        self.assertEqual(2, len(report["missing_sources"]))

    def test_error_and_unresolved_citations_fail(self):
        from agent.retrieval import assess
        report = assess("quality", {
            "activity": [{"id": 1, "error": {"code": "Forbidden"}}],
            "response": [{"content": [{"type": "text", "text": "답변 [ref_id:missing]"}]}],
        }, 200)
        self.assertFalse(report["passed"])
        self.assertEqual(["missing"], report["unresolved_citations"])
        self.assertEqual(["Forbidden"], report["error_codes"])


if __name__ == "__main__":
    unittest.main()
