"""05의 KB 계약. 토큰이나 원문을 포함하지 않는 근거 요약을 반환합니다."""

import os
import re
from typing import Any, Literal

ReasoningEffort = Literal["low", "medium"]

SOURCES = {
    "process": {
        "ks-process-mes-v2": "mcpServer",
        "ks-process-webiq-v2": "mcpServer",
        "ks-quality-manuals-v2": "azureBlob",
    },
    "quality": {
        "ks-quality-handovers-v2": "searchIndex",
        "ks-quality-workorders-v2": "searchIndex",
        "ks-quality-fabric-v2": "fabricDataAgent",
        "ks-quality-workiq-v2": "workIQ",
    },
}


def kb_name(kb: str) -> str:
    if kb not in SOURCES:
        raise ValueError("공정 또는 품질 KB를 선택하세요.")
    names = {
        "process": os.getenv("PROCESS_KB_NAME", "process-assistance-kb-v2"),
        "quality": os.getenv("QUALITY_KB_NAME", "quality-investigation-kb-v2"),
    }
    if not re.fullmatch(r"[a-z0-9-]+", names[kb]):
        raise ValueError("KB 이름 형식이 올바르지 않습니다.")
    return names[kb]


def search_endpoint() -> str:
    endpoint = os.environ.get("SEARCH_ENDPOINT", "").rstrip("/")
    if not re.fullmatch(r"https://[a-z0-9-]+\.search\.windows\.net", endpoint):
        raise ValueError("SEARCH_ENDPOINT는 HTTPS Azure AI Search 주소여야 합니다.")
    return endpoint


def make_request(kb: str, question: str, search_token: str, workiq_token: str,
                 *, reasoning_effort: ReasoningEffort = "medium"):
    name = kb_name(kb)
    if reasoning_effort not in ("low", "medium"):
        raise ValueError("Foundry IQ 추론 강도는 low 또는 medium이어야 합니다.")
    if not question.strip() or len(question) > 6000:
        raise ValueError("질문은 1~6000자여야 합니다.")
    if not search_token or (kb == "quality" and not workiq_token):
        raise ValueError("필요한 사용자 위임 토큰이 없습니다. 다시 로그인하세요.")
    headers = {"Authorization": f"Bearer {search_token}"}
    if kb == "quality":
        headers["x-ms-query-source-authorization"] = search_token
        headers["x-ms-query-work-iq-source-authorization"] = workiq_token
    body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
        "knowledgeSourceParams": [
            {"knowledgeSourceName": name, "kind": kind,
             "includeReferences": True, "includeReferenceSourceData": True}
            for name, kind in SOURCES[kb].items()
        ],
        "includeActivity": True,
        "retrievalReasoningEffort": {"kind": reasoning_effort},
        "maxRuntimeInSeconds": 300,
    }
    return f"/knowledgebases/{name}/retrieve", body, headers


def answer_text(result: dict[str, Any]) -> str:
    return "\n".join(
        part["text"] for message in result.get("response", [])
        for part in message.get("content", []) if part.get("type") == "text"
    )


def assess(kb: str, result: dict[str, Any], http_status: int) -> dict[str, Any]:
    activities = result.get("activity") or []
    references = result.get("references") or []
    citations = set(re.findall(r"\[ref_id:([^\]]+)\]", answer_text(result)))
    reference_ids = {str(ref.get("id")) for ref in references}
    sources = []
    for name in SOURCES[kb]:
        calls = [a for a in activities if a.get("knowledgeSourceName") == name]
        ids = {str(a["id"]) for a in calls if a.get("id") is not None and (a.get("count") or 0) > 0}
        refs = [ref for ref in references if str(ref.get("activitySource")) in ids]
        sources.append({
            "name": name, "calls": len(calls), "references": len(refs),
            "cited": sum(str(ref.get("id")) in citations for ref in refs),
            "ok": bool(refs) and not any(a.get("error") for a in calls),
        })
    errors = [str(a["error"].get("code", "source_error"))
              if isinstance(a["error"], dict) else "source_error"
              for a in activities if a.get("error")]
    missing = [s["name"] for s in sources if not s["ok"]]
    unresolved = sorted(citations - reference_ids)
    return {
        "kb": kb, "http_status": http_status, "sources": sources, "missing_sources": missing,
        "error_codes": errors, "warning_count": sum(bool(a.get("warning")) for a in activities),
        "unresolved_citations": unresolved, "reference_ids": sorted(reference_ids),
        "passed": http_status == 200 and bool(answer_text(result).strip())
        and not errors and not missing and not unresolved and bool(citations),
    }
