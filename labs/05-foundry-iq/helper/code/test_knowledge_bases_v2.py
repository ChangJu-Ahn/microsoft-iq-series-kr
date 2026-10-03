from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import Mock


MODULE = Path(__file__).with_name("knowledge_bases_v2.py")


class KnowledgeBasesV2Tests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.exists(), "v2 생성·검증 모듈이 필요합니다.")
        spec = importlib.util.spec_from_file_location("knowledge_bases_v2", MODULE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_sources_and_bases_are_new_and_suffixed(self):
        self.assertEqual(len(self.module.SOURCE_NAMES), 7)
        self.assertEqual(len(self.module.BASE_NAMES), 2)
        names = self.module.SOURCE_NAMES + self.module.BASE_NAMES
        self.assertTrue(all(name.endswith("-v2") for name in names))
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn("ks-fabriciq-factoryagent-v2", names)

    def test_clone_does_not_mutate_original(self):
        original = {
            "@odata.etag": "old",
            "name": "old-source",
            "kind": "searchIndex",
            "searchIndexParameters": {"searchIndexName": "existing-index"},
        }
        cloned = self.module.clone_source(original, "ks-quality-workorders-v2")
        self.assertEqual(original["name"], "old-source")
        self.assertEqual(cloned["searchIndexParameters"], original["searchIndexParameters"])
        self.assertNotIn("@odata.etag", cloned)
        cloned["searchIndexParameters"]["searchIndexName"] = "changed"
        self.assertEqual(original["searchIndexParameters"]["searchIndexName"], "existing-index")

    def test_mes_allows_only_read_tools(self):
        source = self.module.mcp_sources("test-mes-key", "test-web-key")[0]
        names = {tool["name"] for tool in source["mcpServerParameters"]["tools"]}
        self.assertLessEqual(len(names), 5)
        self.assertEqual(names, {
            "get_lot", "get_process_route", "list_process_results",
            "list_products", "list_equipments",
        })

    def test_webiq_is_actual_webiq_and_only_web_tool(self):
        source = self.module.mcp_sources("test-mes-key", "test-web-key")[1]
        self.assertEqual(source["kind"], "mcpServer")
        params = source["mcpServerParameters"]
        self.assertEqual(params["serverURL"], "https://api.microsoft.ai/v3/mcp")
        self.assertEqual([tool["name"] for tool in params["tools"]], ["web"])
        self.assertEqual(params["authentication"]["storedHeadersParameters"]["headers"],
                         {"x-apikey": "test-web-key"})

    def test_build_uses_existing_data_but_new_definitions(self):
        originals = {
            name: {"name": name, "kind": "searchIndex"}
            for name in self.module.CLONES
        }
        originals["ks-azureblob-manual"] = {
            "name": "ks-azureblob-manual", "kind": "azureBlob",
            "azureBlobParameters": {
                "containerName": "manuals", "connectionString": "<redacted>",
                "createdResources": {"index": "old-index"},
                "ingestionParameters": {
                    "embeddingModel": {"azureOpenAIParameters": {"apiKey": "<redacted>"}},
                },
            },
        }
        sources, bases = self.module.build_definitions(
            originals, {"models": []}, "/subscriptions/test/storage/account",
            "mes-test", "web-test",
        )
        self.assertEqual({s["name"] for s in sources}, set(self.module.SOURCE_NAMES))
        self.assertEqual([len(b["knowledgeSources"]) for b in bases], [3, 4])
        process_names = {s["name"] for s in bases[0]["knowledgeSources"]}
        quality_names = {s["name"] for s in bases[1]["knowledgeSources"]}
        self.assertEqual(process_names, {
            "ks-process-mes-v2", "ks-process-webiq-v2", "ks-quality-manuals-v2",
        })
        self.assertEqual(quality_names, {
            "ks-quality-handovers-v2", "ks-quality-workorders-v2",
            "ks-quality-fabric-v2", "ks-quality-workiq-v2",
        })
        self.assertFalse(process_names & quality_names)
        self.assertIn("매뉴얼", bases[0]["retrievalInstructions"])
        self.assertNotIn("manuals", bases[1]["retrievalInstructions"])
        blob = next(s for s in sources if s["kind"] == "azureBlob")
        params = blob["azureBlobParameters"]
        self.assertNotIn("createdResources", params)
        self.assertEqual(params["connectionString"], "ResourceId=/subscriptions/test/storage/account;")
        self.assertIsNone(params["ingestionParameters"]["embeddingModel"]["azureOpenAIParameters"]["apiKey"])
        self.assertEqual(originals["ks-azureblob-manual"]["azureBlobParameters"]["connectionString"], "<redacted>")

    def test_create_only_rejects_existing_before_any_write(self):
        session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"value": [{"name": "ks-process-mes-v2"}]}
        session.get.return_value = response
        with self.assertRaisesRegex(RuntimeError, "이미 존재"):
            self.module.create_only(session, "https://example.search.windows.net",
                                    [{"name": "ks-process-mes-v2"}], [])
        session.put.assert_not_called()

    def test_create_uses_atomic_no_overwrite(self):
        session = Mock()
        response = Mock(status_code=200)
        response.json.return_value = {"value": []}
        session.get.return_value = response
        session.put.return_value = Mock(status_code=201)
        with redirect_stdout(io.StringIO()):
            self.module.create_only(session, "https://example.search.windows.net",
                                    [{"name": "ks-process-mes-v2"}], [])
        self.assertEqual(session.put.call_args.kwargs["headers"]["If-None-Match"], "*")

    def test_unapproved_name_rejected_without_network(self):
        session = Mock()
        with self.assertRaises(ValueError):
            self.module.create_only(session, "https://example.search.windows.net",
                                    [{"name": "manufacturing-kb"}], [])
        session.get.assert_not_called()
        session.put.assert_not_called()

    def test_evidence_requires_references_and_no_errors(self):
        result = {
            "activity": [{"id": 1, "knowledgeSourceName": "ks-process-webiq-v2", "count": 3}],
            "references": [{"activitySource": 1}],
        }
        self.assertTrue(self.module.has_evidence(result, "ks-process-webiq-v2"))
        self.assertFalse(self.module.has_evidence(result, "ks-process-mes-v2"))
        result["activity"][0]["error"] = {"message": "failed"}
        self.assertFalse(self.module.has_evidence(result, "ks-process-webiq-v2"))
        result["activity"][0].pop("error")
        result["references"] = []
        self.assertFalse(self.module.has_evidence(result, "ks-process-webiq-v2"))

    def test_zero_results_are_not_evidence_even_with_reference(self):
        result = {
            "activity": [{"id": 1, "knowledgeSourceName": "ks-process-webiq-v2", "count": 0}],
            "references": [{"activitySource": 1}],
        }
        self.assertFalse(self.module.has_evidence(result, "ks-process-webiq-v2"))


if __name__ == "__main__":
    unittest.main()
