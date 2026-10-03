"""로그인 사용자가 읽을 수 있는 KB/KS의 설명만 브라우저에 전달합니다."""

import asyncio
import re

import httpx

from agent.retrieval import kb_name, search_endpoint


async def fetch_catalog(kb: str, token: str, client: httpx.AsyncClient) -> dict:
    endpoint = search_endpoint()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"api-version": "2026-08-01-preview"}

    async def read(path: str):
        response = await client.get(endpoint + path, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    base = await read(f"/knowledgebases/{kb_name(kb)}")
    names = [source["name"] for source in base["knowledgeSources"]]
    if any(not re.fullmatch(r"[a-z0-9-]+", name) for name in names):
        raise ValueError("연결된 KS 이름 형식이 올바르지 않습니다.")
    definitions = await asyncio.gather(*(read(f"/knowledgesources/{name}") for name in names))
    return {
        "name": base["name"], "description": base.get("description"),
        "default_reasoning_effort": (base.get("retrievalReasoningEffort") or {}).get("kind"),
        "sources": [
            {"name": source["name"], "kind": source["kind"], "description": source.get("description")}
            for source in definitions
        ],
    }
