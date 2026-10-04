"""같은 retrieve 응답을 05 노트북 파서로 해석합니다. 추가 모델/API 호출은 없습니다."""

import json
import re
from typing import Any

from retrieval_trace import parse_trace

SOURCE_CONTENT_LIMIT = 12000
CONTENT_FIELDS = ("fabricAnswer", "snippet", "chunk", "content", "text", "page_content", "body")
METADATA_FIELDS = ("uid", "id", "chunk_id", "parent_id", "document_id", "title",
                   "name", "url", "blob_url", "file_name", "path")


def redact_debug(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if any(part in key.lower().replace("-", "").replace("_", "")
                                    for part in ("authorization", "token", "secret", "apikey",
                                                 "headers", "connectionstring"))
            and key not in {"inputTokens", "outputTokens", "reasoningTokens", "totalTokens"} else redact_debug(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_debug(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [REDACTED]", value)
        return re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED]", value)
    return value


def source_content(value: Any, path: str = "sourceData", *, structured: bool = False,
                   depth: int = 0) -> tuple[str, str, str] | None:
    if depth > 8:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        if value.lstrip().startswith(("{", "[")):
            try:
                decoded = redact_debug(json.loads(value))
            except json.JSONDecodeError:
                return (value, path, "text") if structured else None
            return source_content(decoded, path, structured=structured, depth=depth + 1)
        return value, path, "text"
    if isinstance(value, dict):
        for key in CONTENT_FIELDS:
            if key in value:
                result = source_content(value[key], f"{path}.{key}", structured=True, depth=depth + 1)
                if result:
                    return result
        if isinstance(value.get("parts"), list):
            result = source_content(value["parts"], f"{path}.parts", depth=depth + 1)
            if result:
                return result
        if structured and value:
            return json.dumps(redact_debug(value), ensure_ascii=False, indent=2), path, "json"
    if isinstance(value, list):
        parts = [result for item in value
                 if (result := source_content(item, path, depth=depth + 1))]
        if parts:
            return "\n\n".join(part[0] for part in parts), path, "text"
        if structured and value:
            return json.dumps(redact_debug(value), ensure_ascii=False, indent=2), path, "json"
    return None


def debug_trace(result: dict) -> dict:
    trace = parse_trace(redact_debug(result))
    trace.pop("answer")
    for reference in trace["references"]:
        data = reference.pop("sourceData", None)
        content = source_content(data)
        reference["sourceContentStatus"] = "available" if content else "missing" if data is None else "unavailable"
        if isinstance(data, dict):
            reference["sourceMetadata"] = {key: data[key] for key in METADATA_FIELDS if key in data}
        if content:
            text, field, content_format = content
            reference["sourcePreview"] = text[:SOURCE_CONTENT_LIMIT]
            reference["sourceContentField"] = field
            reference["sourceContentFormat"] = content_format
            reference["sourceContentLength"] = len(text)
            reference["sourcePreviewLimit"] = SOURCE_CONTENT_LIMIT
            reference["previewTruncated"] = len(text) > SOURCE_CONTENT_LIMIT
    types = [str(row["type"]).lower() for row in trace["timeline"]]
    trace["available"] = bool(trace["timeline"])
    trace["observed_reasoning_efforts"] = sorted({
        row["retrievalReasoningEffort"]["kind"] for row in result.get("activity", [])
        if isinstance(row.get("retrievalReasoningEffort"), dict)
        and row["retrievalReasoningEffort"].get("kind")
    })
    trace["metrics"] = {
        "planning_passes": sum("queryplanning" in name for name in types),
        "search_calls": len(trace["queries"]),
        "additional_source_calls": len(trace["repeatedQueries"]),
        "synthesis_passes": sum("answersynthesis" in name for name in types),
        "reference_count": len(trace["references"]),
    }
    return trace
