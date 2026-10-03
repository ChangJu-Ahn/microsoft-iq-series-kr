import os
import asyncio
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class WebTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        import web
        self.web = web
        web.sessions.clear()
        self.client = TestClient(web.app, base_url="http://localhost:8000")

    def test_anonymous_cannot_read_questions_or_chat(self):
        self.assertEqual(401, self.client.get("/api/questions").status_code)
        self.assertEqual(401, self.client.post("/api/chat", json={"kb": "process", "question": "q"}).status_code)
        self.assertEqual(401, self.client.get("/api/knowledge-base?kb=process").status_code)

    def test_chat_request_accepts_only_low_or_medium(self):
        from web import ChatRequest
        from pydantic import ValidationError
        self.assertEqual("medium", ChatRequest(kb="quality", question="q").reasoning_effort)
        self.assertEqual("low", ChatRequest(kb="quality", question="q", reasoning_effort="low").reasoning_effort)
        with self.assertRaises(ValidationError):
            ChatRequest(kb="quality", question="q", reasoning_effort="high")

    def test_catalog_only_returns_descriptions_not_connection_secrets(self):
        import httpx
        from catalog import fetch_catalog

        def handler(request):
            self.assertEqual("GET", request.method)
            self.assertEqual("Bearer user-token", request.headers["Authorization"])
            if "/knowledgebases/" in request.url.path:
                data = {"name": "process-assistance-kb-v2", "description": "KB 설명",
                        "retrievalReasoningEffort": {"kind": "medium"},
                        "knowledgeSources": [{"name": "ks-process-mes-v2"}],
                        "models": [{"apiKey": "must-not-leak"}]}
            else:
                data = {"name": "ks-process-mes-v2", "kind": "mcpServer", "description": "KS 설명",
                        "mcpServerParameters": {"headers": {"X-API-Key": "must-not-leak"}}}
            return httpx.Response(200, json=data)

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await fetch_catalog("process", "user-token", client)

        import json
        with patch.dict(os.environ, {"SEARCH_ENDPOINT": "https://demo.search.windows.net"}):
            result = asyncio.run(run())
        self.assertEqual("KB 설명", result["description"])
        self.assertEqual([{"name": "ks-process-mes-v2", "kind": "mcpServer", "description": "KS 설명"}], result["sources"])
        self.assertNotIn("must-not-leak", json.dumps(result))
        self.assertNotIn("models", result)

    def test_catalog_propagates_permission_failure(self):
        import httpx
        from catalog import fetch_catalog

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(
                lambda request: httpx.Response(403, json={"error": "denied"}))) as client:
                return await fetch_catalog("process", "user-token", client)

        with patch.dict(os.environ, {"SEARCH_ENDPOINT": "https://demo.search.windows.net"}), self.assertRaises(httpx.HTTPStatusError):
            asyncio.run(run())

    def test_home_is_available_and_has_no_inline_code(self):
        response = self.client.get("/")
        self.assertEqual(200, response.status_code)
        self.assertIn("Entra ID", response.text)
        self.assertIn("default-src 'self'", response.headers["content-security-policy"])

    def test_knowledge_context_is_a_sidebar_not_an_exclusive_tab(self):
        response = self.client.get("/")
        self.assertIn('class="workspace-layout"', response.text)
        self.assertIn('<aside id="catalog-panel"', response.text)
        self.assertIn('<h2 id="catalog-heading">Knowledge Base</h2>', response.text)
        self.assertNotIn('role="tab"', response.text)
        self.assertNotIn('id="catalog-panel" hidden', response.text)

    def test_workshop_questions_are_selectable_and_text_remains_editable(self):
        response = self.client.get("/")
        self.assertIn('id="sample"', response.text)
        self.assertIn('aria-haspopup="dialog"', response.text)
        self.assertIn('<dialog id="question-dialog"', response.text)
        self.assertIn('05 실습 질문 보기', response.text)
        self.assertIn('<textarea id="question"', response.text)
        self.assertNotIn('<select id="sample"', response.text)

    def test_question_api_returns_current_notebook_catalog(self):
        from questions import load_questions
        self.web.sessions["questions"] = {
            "expires": time.time() + 60,
            "account": {"username": "test@example.test"},
        }
        self.client.cookies.set("iq_session", "questions")
        response = self.client.get("/api/questions")
        self.assertEqual(200, response.status_code)
        self.assertEqual(load_questions(), response.json())
        self.assertEqual(["process"] * 3 + ["quality"] * 4,
                         [question["kb"] for question in response.json()])

    def test_callback_rejects_unknown_state(self):
        self.assertEqual(400, self.client.get("/auth/callback?state=forged&code=bogus").status_code)

    def test_session_expires(self):
        self.web.sessions["expired"] = {"expires": time.time() - 1, "account": {"username": "demo"}}
        self.client.cookies.set("iq_session", "expired")
        self.assertEqual(401, self.client.get("/api/me").status_code)
        self.assertNotIn("expired", self.web.sessions)

    def test_cross_origin_chat_and_logout_are_forbidden(self):
        self.web.sessions["valid"] = {"expires": time.time() + 60, "account": {"username": "demo"}, "csrf": "csrf"}
        self.client.cookies.set("iq_session", "valid")
        headers = {"origin": "https://evil.example", "x-csrf-token": "csrf"}
        self.assertEqual(403, self.client.post("/api/chat", headers=headers, json={"kb": "process", "question": "q"}).status_code)
        self.assertEqual(403, self.client.post("/auth/logout", headers=headers).status_code)

    def test_logout_removes_session(self):
        self.web.sessions["valid"] = {"expires": time.time() + 60, "account": {"username": "demo"}, "csrf": "csrf"}
        self.client.cookies.set("iq_session", "valid")
        response = self.client.post("/auth/logout", headers={"origin": "http://localhost:8000", "x-csrf-token": "csrf"})
        self.assertEqual(200, response.status_code)
        self.assertNotIn("valid", self.web.sessions)

    def test_busy_reservation_precedes_token_fetch_and_is_released_on_failure(self):
        from fastapi import HTTPException
        import httpx

        self.web.sessions["valid"] = {"expires": time.time() + 60, "account": {"username": "demo"}, "csrf": "csrf"}
        headers = {"origin": "http://localhost:8000", "x-csrf-token": "csrf", "cookie": "iq_session=valid"}

        async def run():
            entered = asyncio.Event()
            release = asyncio.Event()

            async def blocked_token(*args):
                entered.set()
                await release.wait()
                raise HTTPException(401, "expired")

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.web.app), base_url="http://localhost:8000") as client:
                with patch("web.asyncio.to_thread", side_effect=blocked_token):
                    first = asyncio.create_task(client.post("/api/chat", headers=headers, json={"kb": "process", "question": "q"}))
                    await entered.wait()
                    second = asyncio.create_task(client.post("/api/chat", headers=headers, json={"kb": "process", "question": "q"}))
                    await asyncio.sleep(0.03)
                    release.set()
                    return await asyncio.gather(first, second)

        responses = asyncio.run(run())
        self.assertEqual([401, 429], [r.status_code for r in responses])
        self.assertFalse(self.web.sessions["valid"].get("busy", False))


if __name__ == "__main__":
    unittest.main()
