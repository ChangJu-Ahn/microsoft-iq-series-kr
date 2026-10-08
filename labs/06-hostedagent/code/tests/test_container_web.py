import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class ContainerWebTests(unittest.TestCase):
    def test_deployed_static_verification_includes_nested_demo_files(self):
        import httpx
        from deploy_web import verify_static_assets
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "demo").mkdir()
            (root / "index.html").write_bytes(b"home")
            (root / "demo/mail.json").write_bytes(b'{"messages":[]}')
            (root / "demo/fabric-new.png").write_bytes(b"image")
            expected = {"/static/index.html": b"home",
                        "/static/demo/mail.json": b'{"messages":[]}',
                        "/static/demo/fabric-new.png": b"image"}
            seen = []

            def handler(request):
                seen.append(request.url.path)
                return httpx.Response(200, content=expected[request.url.path])

            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                verify_static_assets(client, "https://demo.example.com", root)
            self.assertEqual(set(expected), set(seen))
            with httpx.Client(transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=b"old-revision")
            )) as client, self.assertRaisesRegex(RuntimeError, "빌드 context"):
                verify_static_assets(client, "https://demo.example.com", root)

    def test_questions_module_imports_from_shallow_container_path(self):
        source = (ROOT / "questions.py").read_text()
        namespace = {"__file__": "/app/questions.py"}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "questions.json"
            target.write_text('[{"kb":"process","question":"LOT0012"}]')
            with patch.dict(os.environ, {"QUESTION_SET_PATH": str(target)}):
                exec(compile(source, "/app/questions.py", "exec"), namespace)
                self.assertEqual([{"kb": "process", "question": "LOT0012"}], namespace["load_questions"]())

    def test_deployment_waits_for_new_ready_revision_not_old_healthy_one(self):
        from deploy_web import wait_for_revision
        from unittest.mock import Mock
        read = Mock(side_effect=[
            {"latest": "new", "ready": "old", "image": "image:new", "state": "Succeeded"},
            {"latest": "new", "ready": "new", "image": "image:new", "state": "Succeeded"}
        ])
        with patch("deploy_web.time.sleep"):
            self.assertEqual("new", wait_for_revision(read, "image:new"))
        self.assertEqual(2, read.call_count)

    def test_deployment_rejects_a_failed_revision(self):
        from deploy_web import wait_for_revision
        with self.assertRaises(RuntimeError):
            wait_for_revision(lambda: {"state": "Failed", "latest": "new", "ready": "old",
                                      "image": "image:new"}, "image:new")

    def test_cloud_identity_takes_priority_over_local_subscription(self):
        from web import backend_credential
        with patch.dict(os.environ, {"IDENTITY_ENDPOINT": "http://identity", "AZURE_CLIENT_ID": "client-id",
                                     "AZURE_SUBSCRIPTION_ID": "local-sub"}):
            with patch("web.ManagedIdentityCredential") as identity, patch("web.AzureCliCredential") as cli:
                backend_credential()
                identity.assert_called_once_with(client_id="client-id")
                cli.assert_not_called()

    def test_local_cli_auth_is_preserved(self):
        from web import backend_credential
        with patch.dict(os.environ, {"AZURE_SUBSCRIPTION_ID": "local-sub"}, clear=True):
            with patch("web.AzureCliCredential") as cli:
                backend_credential()
                cli.assert_called_once_with(subscription="local-sub")

    def test_packaged_questions_match_original_notebook(self):
        from questions import load_questions
        original = load_questions()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "questions.json"
            target.write_text(json.dumps(original))
            with patch.dict(os.environ, {"QUESTION_SET_PATH": str(target)}):
                with patch("questions.ast.parse", side_effect=AssertionError("must use package")):
                    self.assertEqual(original, load_questions())

    def test_build_context_excludes_notebooks_secrets_logs_and_agent_runtime(self):
        from deploy_web import build_context
        from questions import load_questions
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            digest = build_context(target)
            files = {str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()}
            self.assertEqual(64, len(digest))
            self.assertIn("agent/retrieval.py", files)
            self.assertIn("notebook-questions.json", files)
            self.assertIn("static/demo/recordings.json", files)
            self.assertIn("static/demo/mail.json", files)
            for name in ["iq-settings.json", "foundry-process.png", "foundry-quality.png",
                         "fabric-legacy.png", "fabric-new.png"]:
                self.assertIn(f"static/demo/{name}", files)
                self.assertIn(f"!static/demo/{name}", (target / ".dockerignore").read_text())
            self.assertIn("static/mail.html", files)
            self.assertIn("static/tour.js", files)
            self.assertIn("static/tour.css", files)
            dockerignore = (target / ".dockerignore").read_text()
            self.assertIn("!static/demo/", dockerignore)
            self.assertIn("!static/demo/recordings.json", dockerignore)
            self.assertIn("!static/demo/mail.json", dockerignore)
            self.assertFalse(any(".env" in p or p.endswith(".ipynb") or p.startswith("logs/") for p in files))
            self.assertNotIn("agent/main.py", files)
            self.assertEqual(load_questions(), json.loads((target / "notebook-questions.json").read_text()))

    def test_invalid_packaged_questions_fail_explicitly(self):
        from questions import load_questions
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "questions.json"
            target.write_text('[{"kb":"unknown","question":""}]')
            with patch.dict(os.environ, {"QUESTION_SET_PATH": str(target)}), self.assertRaises(ValueError):
                load_questions()

    def test_probe_does_not_require_login_or_call_backend(self):
        from fastapi.testclient import TestClient
        from web import app
        response = TestClient(app).get("/healthz")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok"}, response.json())

    def test_https_origin_sets_secure_cookie_and_hsts(self):
        from fastapi.testclient import TestClient
        from fastapi.responses import JSONResponse
        from web import app, set_cookie
        with patch.dict(os.environ, {"WEB_ORIGIN": "https://demo.example.com"}):
            response = JSONResponse({"ok": True})
            set_cookie(response, "opaque-session")
            self.assertIn("Secure", response.headers["set-cookie"])
            self.assertIn("HttpOnly", response.headers["set-cookie"])
            health = TestClient(app).get("/healthz")
            self.assertEqual("max-age=31536000", health.headers["strict-transport-security"])


if __name__ == "__main__":
    unittest.main()
