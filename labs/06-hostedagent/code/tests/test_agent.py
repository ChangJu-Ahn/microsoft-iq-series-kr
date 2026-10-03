import asyncio
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "05-foundry-iq/helper/code"))


class AgentTests(unittest.TestCase):
    def test_invocation_validates_effort_and_defaults_to_medium(self):
        from main import Invocation
        from pydantic import ValidationError
        self.assertEqual("medium", Invocation(kb="process", question="q").reasoning_effort)
        self.assertEqual("low", Invocation(kb="process", question="q", reasoning_effort="low").reasoning_effort)
        with self.assertRaises(ValidationError):
            Invocation(kb="process", question="q", reasoning_effort="high")

    def test_effort_is_forwarded_and_latency_phases_are_separate(self):
        from main import stream_answer
        now = [100.0]
        received = []

        async def retrieve(*args, **kwargs):
            received.append((args, kwargs))
            now[0] += 3
            return {"response": [{"content": [{"type": "text", "text": "근거"}]}],
                    "activity": [{"type": "agenticReasoning", "retrievalReasoningEffort": {"kind": "low"}}]}, 200

        async def generate(*args):
            now[0] += 2
            yield "답"
            now[0] += 1
            yield "변"

        async def run():
            with patch("main.time.monotonic", side_effect=lambda: now[0]):
                return [chunk async for chunk in stream_answer(
                    "process", "q", "s", "", reasoning_effort="low", retrieve=retrieve, generate=generate)]

        chunks = asyncio.run(run())
        data = json.loads(chunks[-1].splitlines()[1][6:])
        self.assertEqual("low", received[0][1]["reasoning_effort"])
        self.assertEqual("low", data["reasoning_effort"])
        self.assertEqual(3, data["retrieval_seconds"])
        self.assertEqual(3, data["generation_seconds"])
        self.assertEqual(5, data["first_delta_seconds"])
        self.assertEqual(6, data["elapsed_seconds"])
        trace = next(json.loads(c.splitlines()[1][6:]) for c in chunks if c.startswith("event: trace"))
        self.assertEqual("low", trace["requested_reasoning_effort"])
        self.assertEqual(["low"], trace["observed_reasoning_efforts"])

    def test_quality_instructions_do_not_use_process_source_labels(self):
        from main import answer_instructions
        self.assertIn("공개 기술 설명", answer_instructions("process"))
        self.assertIn("내부 조치 이력", answer_instructions("quality"))
        self.assertNotIn("공개 기술 설명", answer_instructions("quality"))

    def test_missing_headers_rejected_before_stream(self):
        from main import validate_request
        with self.assertRaises(ValueError):
            validate_request({"kb": "quality", "question": "질문"}, {})

    def test_tokens_are_not_accepted_in_payload(self):
        from main import Invocation
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            Invocation(kb="process", question="질문", search_token="secret")

    def test_sse_json_preserves_multiline_text(self):
        from main import event
        payload = event("delta", {"text": "첫째\n둘째"})
        self.assertEqual("event: delta", payload.splitlines()[0])
        self.assertEqual({"text": "첫째\n둘째"}, json.loads(payload.splitlines()[1][6:]))

    def test_stream_really_forwards_model_deltas(self):
        from main import stream_answer

        async def retrieve(*args, **kwargs):
            return {"response": [{"content": [{"type": "text", "text": "근거 [ref_id:0]"}]}]}, 200

        async def generate(*args):
            yield "첫"
            yield "답변"

        async def run():
            return [chunk async for chunk in stream_answer(
                "process", "질문", "s", "", retrieve=retrieve, generate=generate)]

        chunks = asyncio.run(run())
        self.assertIn("event: status", chunks[0])
        self.assertEqual(2, sum("event: delta" in c for c in chunks))
        self.assertEqual(1, sum("event: trace" in c for c in chunks))
        self.assertIn("event: done", chunks[-1])

    def test_model_failure_is_terminal_error(self):
        from main import stream_answer
        import httpx

        async def retrieve(*args, **kwargs):
            raise httpx.ReadTimeout("must not leak private diagnostic")

        async def run():
            return [chunk async for chunk in stream_answer(
                "process", "질문", "s", "", retrieve=retrieve)]

        chunks = asyncio.run(run())
        self.assertIn("event: error", chunks[-1])
        self.assertNotIn("must not leak", "".join(chunks))
        self.assertNotIn("event: done", "".join(chunks))


if __name__ == "__main__":
    unittest.main()
