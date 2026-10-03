import os
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

CODE = Path(__file__).resolve().parents[1]
LAB = CODE.parent
sys.path.insert(0, str(CODE))


class LayoutTests(unittest.TestCase):
    def test_all_sources_and_deployment_inputs_live_under_code(self):
        for name in ["web.py", "catalog.py", "questions.py", "deploy.py", "deploy_web.py",
                     "evaluate.py", "setup_identity.py", "Dockerfile", ".dockerignore",
                     ".env.example", "requirements.txt", "requirements-web.txt",
                     "agent", "static", "tests", "infra"]:
            with self.subTest(name=name):
                self.assertTrue((CODE / name).exists())
                self.assertFalse((LAB / name).exists())

    def test_original_notebook_is_resolved_from_relocated_code(self):
        from questions import NOTEBOOK, load_questions
        self.assertEqual(LAB.parent / "05-foundry-iq/kb_retrieve_test.ipynb", NOTEBOOK)
        self.assertEqual({"process", "quality"}, {q["kb"] for q in load_questions()})

    def test_packaging_does_not_depend_on_current_working_directory(self):
        from deploy_web import build_context
        from questions import load_questions
        import json
        expected = load_questions()
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "image"
            target.mkdir()
            try:
                os.chdir(temporary)
                build_context(target)
            finally:
                os.chdir(original_cwd)
            with patch.dict(os.environ, {"QUESTION_SET_PATH": str(target / "notebook-questions.json")}):
                self.assertEqual(expected, load_questions())
            self.assertEqual(expected, json.loads((target / "notebook-questions.json").read_text()))
            self.assertNotIn("logs", {p.name for p in target.iterdir()})

    def test_agent_package_resolves_shared_parser_and_writes_logs_above_code(self):
        import deploy
        from types import SimpleNamespace

        uploaded = []

        def create_version(**kwargs):
            uploaded.append(kwargs["code"].read())
            return SimpleNamespace(version="test")

        with patch("deploy.load_dotenv"), patch("deploy.AzureCliCredential"), \
                patch("deploy.AIProjectClient") as client, \
                patch.object(Path, "write_text", autospec=True, return_value=0) as write, \
                patch.dict(os.environ, {
                    "AZURE_SUBSCRIPTION_ID": "test",
                    "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/test",
                    "HOSTED_AGENT_NAME": "test",
                    "AZURE_AI_MODEL_DEPLOYMENT_NAME": "test",
                    "SEARCH_ENDPOINT": "https://example.search.windows.net",
                }):
            agents = client.return_value.__enter__.return_value.agents
            agents.create_version_from_code.side_effect = create_version
            agents.get_version.return_value = {"status": "active"}
            agents.download_code.side_effect = lambda **kwargs: uploaded
            deploy.main()

        with zipfile.ZipFile(io.BytesIO(uploaded[0])) as archive:
            self.assertEqual({"main.py", "retrieval.py", "trace_view.py", "requirements.txt",
                              "retrieval_trace.py"}, set(archive.namelist()))
            helper = LAB.parent / "05-foundry-iq/helper/code/retrieval_trace.py"
            self.assertEqual(helper.read_bytes(), archive.read("retrieval_trace.py"))
        self.assertTrue(write.call_args_list)
        self.assertTrue(all(call.args[0] == LAB / "logs/deployment.json" for call in write.call_args_list))


if __name__ == "__main__":
    unittest.main()
