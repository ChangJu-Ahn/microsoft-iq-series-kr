from contextlib import chdir, redirect_stdout
import ast
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import requests


LAB = Path(__file__).resolve().parents[2]
NOTEBOOK = LAB / "kb_retrieve_test.ipynb"
PROCESS_SOURCES = {"ks-process-mes-v2", "ks-process-webiq-v2", "ks-quality-manuals-v2"}
QUALITY_SOURCES = {
    "ks-quality-handovers-v2", "ks-quality-workorders-v2",
    "ks-quality-fabric-v2", "ks-quality-workiq-v2",
}


class NotebookV2Tests(unittest.TestCase):
    def test_process_question_matches_requested_lot_investigation(self):
        expected = (
            "MES에서 LOT0012 로트 상태를 확인하고, 현재 진행 중인 공정에서 이슈가 있는지 확인해보자. "
            "만약 이슈가 있다면, 바로 직전 공정의 설비를 확인해서 해당 설비를 내부 장비 문서를 통해서 "
            "어떤 이슈가 있을법한지 검토해 보고, 이 이슈 사항이 웹 상에서 다른 회사에서도 문제가 "
            "발생했는지 퍼블릭하게 확인해서 전체적인 요약본을 제공해"
        )
        _, calls, _ = self.run_notebook()
        self.assertEqual(expected, calls[0].kwargs["json"]["messages"][0]["content"][0]["text"])

    def test_replaced_process_question_has_no_stale_saved_output(self):
        for cell in self.cells:
            if cell.get("id") in ("v2-process-call", "v2-process-trace"):
                self.assertEqual([], cell["outputs"])
                self.assertIsNone(cell["execution_count"])

    def setUp(self):
        self.cells = json.loads(NOTEBOOK.read_text())["cells"]
        self.expected_kbs = []
        for cell in self.cells:
            source = "".join(cell["source"])
            if cell["cell_type"] != "code" or source.lstrip().startswith("%"):
                continue
            for node in ast.parse(source).body:
                if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "retrieve_v2_trace"):
                    self.expected_kbs.append(node.value.args[0].id)
        self.assertEqual({"PROCESS_KB_NAME", "QUALITY_KB_NAME"}, set(self.expected_kbs))
        self.auth = Mock()
        self.auth.acquire_token_interactive.return_value = {"access_token": "test-workiq-token"}
        self.auth.get_accounts.return_value = [{"username": "test@example.test"}]
        self.auth.acquire_token_silent.return_value = {"access_token": "test-search-token"}

    def run_notebook(self, status=200, environment=None, sources_with_errors=()):
        namespace = {}
        output = io.StringIO()

        def retrieve(url, **kwargs):
            sources = kwargs["json"]["knowledgeSourceParams"]
            result = {
                "activity": [
                    {"id": i, "type": source["kind"],
                     "knowledgeSourceName": source["knowledgeSourceName"], "count": 1,
                     **({"error": {"message": "test failure"}}
                        if source["knowledgeSourceName"] in sources_with_errors else {})}
                    for i, source in enumerate(sources)
                ],
                "references": [{"id": str(i), "activitySource": i}
                               for i in range(len(sources))],
                "response": [{"content": [{"type": "text", "text": "테스트 답변 [ref_id:0]"}]}],
            }
            response = Mock(status_code=status)
            response.json.return_value = result
            if status >= 400:
                response.raise_for_status.side_effect = requests.HTTPError(str(status))
            return response

        with (patch.dict(os.environ, environment or {}, clear=True),
              patch.object(sys, "path", list(sys.path)), chdir(LAB),
              patch("msal.PublicClientApplication", return_value=self.auth),
              patch("requests.post", side_effect=retrieve) as post,
              patch("IPython.display.display"), redirect_stdout(output)):
            for cell in self.cells:
                if cell["cell_type"] != "code":
                    continue
                source = "".join(cell["source"])
                if source.startswith("%pip"):
                    continue
                exec(compile(source, cell["id"], "exec"), namespace)
            for name in ("v2_process_trace", "v2_quality_trace"):
                self.assertIn(name, namespace)
        return namespace, post.call_args_list, output.getvalue()

    def test_only_v2_settings_and_calls_remain(self):
        source = "\n".join("".join(c["source"]) for c in self.cells if c["cell_type"] == "code")
        for old in ("manufacturing-kb", "WORKIQ_KNOWLEDGE_SOURCE",
                    "FABRIC_KNOWLEDGE_SOURCE", "KNOWLEDGE_BASE_NAME", "subprocess", "az login"):
            self.assertTrue(old not in source, f"기존 호출 경로가 남아 있습니다: {old}")
        self.assertIn("PublicClientApplication", source)

    def test_top_to_bottom_executes_all_v2_requests(self):
        namespace, calls, output = self.run_notebook()
        self.assertEqual(len(calls), len(self.expected_kbs))
        bases = {
            "PROCESS_KB_NAME": ("process-assistance-kb-v2", PROCESS_SOURCES),
            "QUALITY_KB_NAME": ("quality-investigation-kb-v2", QUALITY_SOURCES),
        }
        for call, setting in zip(calls, self.expected_kbs):
            kb, sources = bases[setting]
            self.assertTrue(call.args[0].endswith(f"/knowledgebases/{kb}/retrieve"))
            self.assertEqual(call.kwargs["headers"]["Authorization"], "Bearer test-search-token")
            body = call.kwargs["json"]
            self.assertEqual({s["knowledgeSourceName"] for s in body["knowledgeSourceParams"]}, sources)
            self.assertTrue(body["includeActivity"])
            self.assertTrue(all(s["includeReferences"] and s["includeReferenceSourceData"]
                                for s in body["knowledgeSourceParams"]))
            self.assertEqual(call.kwargs["timeout"], 330)
            if setting == "QUALITY_KB_NAME":
                self.assertEqual(call.kwargs["headers"]["x-ms-query-work-iq-source-authorization"],
                                 "test-workiq-token")
                self.assertEqual(call.kwargs["headers"]["x-ms-query-source-authorization"],
                                 "test-search-token")
            else:
                self.assertNotIn("x-ms-query-work-iq-source-authorization", call.kwargs["headers"])
        self.assertEqual(namespace["v2_quality_trace"]["unresolvedCitations"], [])
        self.assertNotIn("미확인 또는 실패", output)
        self.auth.acquire_token_interactive.assert_called_once()

    def test_configured_v2_names_are_used_including_quality_headers(self):
        _, calls, _ = self.run_notebook(environment={
            "PROCESS_KB_NAME": "attendee-process-v2",
            "QUALITY_KB_NAME": "attendee-quality-v2",
            "SEARCH_ENDPOINT": "https://example.search.windows.net",
        })
        names = {"PROCESS_KB_NAME": "attendee-process-v2", "QUALITY_KB_NAME": "attendee-quality-v2"}
        self.assertEqual([call.args[0] for call in calls], [
            f"https://example.search.windows.net/knowledgebases/{names[setting]}/retrieve"
            for setting in self.expected_kbs
        ])
        for call, setting in zip(calls, self.expected_kbs):
            if setting == "QUALITY_KB_NAME":
                self.assertIn("x-ms-query-work-iq-source-authorization", call.kwargs["headers"])

    def test_search_token_can_use_interactive_fallback(self):
        self.auth.acquire_token_silent.return_value = None
        self.auth.acquire_token_interactive.side_effect = [
            {"access_token": "test-workiq-token"}, {"access_token": "test-search-token"},
        ]
        _, calls, _ = self.run_notebook()
        self.assertEqual(len(calls), len(self.expected_kbs))
        self.assertEqual(self.auth.acquire_token_interactive.call_count, 2)

    def test_partial_results_and_source_failures_remain_visible(self):
        _, _, output = self.run_notebook(status=206, sources_with_errors={"ks-quality-fabric-v2"})
        self.assertIn("부분 실패", output)
        self.assertIn("ks-quality-fabric-v2 미확인 또는 실패", output)

    def test_http_failure_is_not_returned_as_success(self):
        with self.assertRaises(requests.HTTPError):
            self.run_notebook(status=403)


if __name__ == "__main__":
    unittest.main()
