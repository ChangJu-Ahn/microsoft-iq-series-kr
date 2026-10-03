"""retrieve 응답의 관찰 가능한 실행 기록을 파싱합니다. LLM 호출은 하지 않습니다."""

from datetime import datetime
import json
import re


def redact(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower().replace("-", "").replace("_", "") in {
                "authorization", "apikey", "xapikey", "accesstoken", "refreshtoken",
                "clientsecret", "connectionstring",
            } else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def parse_trace(result: dict) -> dict:
    result = redact(result)
    activities = result.get("activity") or []
    ordered = sorted(
        enumerate(activities),
        key=lambda pair: (
            timestamp(pair[1].get("startedAt")).timestamp()
            if pair[1].get("startedAt") else float("inf"), pair[0],
        ),
    )
    timeline, queries, repeated, overlaps = [], [], [], []
    previous = {}
    for _, activity in ordered:
        start = timestamp(activity.get("startedAt"))
        end = timestamp(activity.get("completedAt"))
        duration = activity.get("elapsedMs")
        duration_basis = "elapsedMs"
        if duration is None:
            duration = round((end - start).total_seconds() * 1000, 3) if start and end else None
            duration_basis = "startedAt/completedAt 차이" if duration is not None else "미제공"
        row = {
            "id": activity.get("id"), "type": activity.get("type"),
            "source": activity.get("knowledgeSourceName"),
            "startedAt": activity.get("startedAt"), "completedAt": activity.get("completedAt"),
            "durationMs": duration, "durationBasis": duration_basis,
            "count": activity.get("count"), "details": activity,
        }
        timeline.append(row)
        if not row["source"]:
            continue
        query = {
            "id": row["id"], "source": row["source"], "count": row["count"],
            "arguments": {key: value for key, value in activity.items() if key.endswith("Arguments")},
            "warning": activity.get("warning"), "error": activity.get("error"),
        }
        queries.append(query)
        prior = previous.get(row["source"])
        if prior:
            repeated.append({
                "source": row["source"], "previousId": prior["id"], "id": row["id"],
                "previousCount": prior["count"], "count": query["count"],
                "argumentsChanged": prior["arguments"] != query["arguments"],
                "reason": "재조회 이유는 응답에 명시되지 않음. 동일 소스 호출만으로 재시도·근거 부족을 단정하지 않습니다.",
            })
        previous[row["source"]] = query
    for index, left in enumerate(timeline):
        for right in timeline[index + 1:]:
            times = [timestamp(row.get(key)) for row in (left, right)
                     for key in ("startedAt", "completedAt")]
            if all(times) and max(times[0], times[2]) < min(times[1], times[3]):
                overlaps.append([left["id"], right["id"]])

    answer = "\n".join(
        content["text"] for message in result.get("response", [])
        for content in message.get("content", []) if content.get("type") == "text"
    )
    citations = set(re.findall(r"\[ref_id:([^\]]+)\]", answer))
    by_id = {str(row["id"]): row for row in timeline if row["id"] is not None}
    references = []
    for reference in result.get("references", []):
        activity = by_id.get(str(reference.get("activitySource")))
        references.append({
            **reference, "source": activity["source"] if activity else None,
            "cited": str(reference.get("id")) in citations,
        })
    return {
        "timeline": timeline, "queries": queries, "repeatedQueries": repeated,
        "overlaps": overlaps, "references": references, "answer": answer,
        "unresolvedCitations": sorted(citations - {str(ref.get("id")) for ref in references}),
    }


def format_trace(trace: dict) -> str:
    def text(value):
        return "미제공" if value is None else str(value)

    def json_text(value):
        return json.dumps(value, ensure_ascii=False, indent=2)

    lines = [
        "1. 실행 타임라인 (내부 추론 전문이 아닌 API 실행 기록)",
        "시작 시각순입니다. 시작 시각 미제공 활동은 뒤에 응답 순서대로 표시합니다.",
        "ID | 활동 | KS | 시작 → 종료 | 소요 ms | 관련 결과 수",
    ]
    for row in trace["timeline"]:
        lines.append(
            f"{row['id']} | {row['type']} | {text(row['source'])} | "
            f"{text(row['startedAt'])} → {text(row['completedAt'])} | "
            f"{text(row['durationMs'])} ({row['durationBasis']}) | {text(row['count'])}"
        )
        details = {
            key: value for key, value in row["details"].items()
            if key not in {"id", "type", "knowledgeSourceName", "startedAt", "completedAt",
                           "elapsedMs", "count"} and not key.endswith("Arguments")
        }
        if details:
            lines.append(json_text(details))
    if not trace["timeline"]:
        lines.append("activity 미제공: includeActivity 설정과 원본 응답을 확인하세요.")
    lines.append("시간이 겹치는 활동 ID 쌍: " + json_text(trace["overlaps"]))
    lines.append("시간 겹침은 관찰값이며 인과관계가 아닙니다. 활동 시간을 합산해 전체 지연으로 해석하지 않습니다.")

    lines.append("\n2. 실제 검색·도구 입력 (원 질문 분할의 실행 결과)")
    for query in trace["queries"]:
        lines.append(json_text(query))
    if not trace["queries"]:
        lines.append("소스 호출 활동 미제공")
    lines.append("count는 관련성 임계값을 통과한 결과 수이며 원본 전체 건수나 최종 인용 수와 다릅니다.")

    lines.append("\n3. 동일 소스 추가 호출")
    for query in trace["repeatedQueries"]:
        lines.append(json_text(query))
    if not trace["repeatedQueries"]:
        lines.append("동일 소스 추가 호출 없음. 계획 활동 반복만으로 재검색을 판정하지 않습니다.")
    lines.append("검색어 변화는 2번의 활동 ID로 대조하세요. warning/error는 관찰 사실이지 재조회 원인의 증명이 아닙니다.")

    lines.append("\n4. 조회 활동 → reference → 최종 답변 인용")
    for ref in trace["references"]:
        lines.append(
            f"활동 {ref.get('activitySource')} / KS {text(ref['source'])} → "
            f"ref_id:{ref.get('id')} → {'최종 답변에 인용' if ref['cited'] else '인용 표식 없음'}"
        )
        metadata = {key: value for key, value in ref.items()
                    if key not in {"sourceData", "source", "cited", "activitySource", "id"}}
        if metadata:
            lines.append(json_text(metadata))
        data = ref.get("sourceData")
        if data is not None:
            preview = json_text(data)
            lines.append("반환 원문 발췌: " + preview[:500] + (" … [500자 미리보기]" if len(preview) > 500 else ""))
    if not trace["references"]:
        lines.append("references 미제공")
    lines.append("연결되지 않은 답변 인용 ID: " + json_text(trace["unresolvedCitations"]))
    lines.append("source가 미제공이면 activity 연결을 확인하세요. sourceData 미제공 시 원문을 추측하지 않습니다.")
    return "\n".join(lines)
