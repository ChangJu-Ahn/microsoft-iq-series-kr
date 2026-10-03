"""노트북의 모든 실제 질문을 Hosted Agent에 호출하고 공유 가능한 측정값만 기록합니다."""

import asyncio
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

from azure.core.exceptions import ClientAuthenticationError
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
import httpx

from questions import load_questions, NOTEBOOK

ROOT = Path(__file__).resolve().parent


async def read_events(response):
    name, data = "", []
    async for line in response.aiter_lines():
        if line.startswith("event:"):
            name = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].strip())
        elif not line and data:
            yield name, json.loads("\n".join(data))
            name, data = "", []
    if data:
        raise ValueError("완료되지 않은 SSE 프레임입니다.")


async def main(efforts: list[str], output: Path):
    load_dotenv(ROOT / ".env")
    questions = [{**case, "reasoning_effort": effort}
                 for case in load_questions() for effort in efforts]
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
        "target": "remote-hosted-agent", "authentication": "Azure CLI delegated user (not browser login)",
        "results": [],
    }
    async with AzureCliCredential(subscription=os.environ["AZURE_SUBSCRIPTION_ID"]) as credential:
        for case in questions:
            row = {"kb": case["kb"], "reasoning_effort": case["reasoning_effort"],
                   "question_sha256": hashlib.sha256(case["question"].encode()).hexdigest()}
            started = time.monotonic()
            chunks = []
            terminal = None
            try:
                ai = await credential.get_token("https://ai.azure.com/.default")
                search = await credential.get_token("https://search.azure.com/.default")
                headers = {"Authorization": f"Bearer {ai.token}", "x-client-search-authorization": search.token}
                if case["kb"] == "quality":
                    work = await credential.get_token(f"api://{os.environ['WORKIQ_APP_ID']}/.default")
                    headers["x-client-workiq-authorization"] = work.token
                async with httpx.AsyncClient(timeout=httpx.Timeout(660, connect=30)) as client:
                    async with client.stream("POST", os.environ["HOSTED_AGENT_ENDPOINT"],
                                             headers=headers, json=case) as response:
                        row["http_status"] = response.status_code
                        response.raise_for_status()
                        row["session_id"] = response.headers.get("x-ms-agent-session-id")
                        async for name, data in read_events(response):
                            if name == "delta":
                                row.setdefault("first_delta_seconds", round(time.monotonic() - started, 3))
                                chunks.append(data["text"])
                            elif name == "evidence":
                                row["retrieval"] = data
                            elif name == "trace":
                                row["trace_metrics"] = data["metrics"]
                                row["trace_available"] = data["available"]
                                row["trace_requested_effort"] = data.get("requested_reasoning_effort")
                                row["observed_reasoning_efforts"] = data.get("observed_reasoning_efforts", [])
                            elif name == "done":
                                terminal = "done"
                                row["completion"] = data
                            elif name == "error":
                                terminal = "error"
                                row["error"] = data
                row["status"] = "passed" if (
                    terminal == "done" and chunks and row["completion"]["evidence"]["passed"]
                    and row.get("trace_available")
                    and row["trace_requested_effort"] == case["reasoning_effort"]
                    and row["completion"].get("reasoning_effort") == case["reasoning_effort"]
                    and all(level == case["reasoning_effort"] for level in row["observed_reasoning_efforts"])
                    and isinstance(row["completion"].get("retrieval_seconds"), (int, float))
                ) else "failed"
            except (ClientAuthenticationError, httpx.HTTPError, ValueError) as exc:
                row["status"] = "blocked" if isinstance(exc, ClientAuthenticationError) else "failed"
                row["error"] = {"code": type(exc).__name__}
            row.update(elapsed_seconds=round(time.monotonic() - started, 3),
                       delta_count=len(chunks), answer_characters=len("".join(chunks)),
                       answer_sha256=hashlib.sha256("".join(chunks).encode()).hexdigest())
            report["results"].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if any(row["status"] != "passed" for row in report["results"]):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efforts", nargs="+", choices=["low", "medium"], default=["medium"])
    parser.add_argument("--output", type=Path, default=Path("../logs/evaluation.json"),
                        help="출력 경로. 상대 경로는 code 폴더 기준입니다.")
    args = parser.parse_args()
    asyncio.run(main(list(dict.fromkeys(args.efforts)), ROOT / args.output))
