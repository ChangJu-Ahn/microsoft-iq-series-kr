import {node} from "./dom.js";

const sources = {
  "ks-process-mes-v2": {label: "MES", kind: "mes"},
  "ks-process-webiq-v2": {label: "Web IQ", kind: "web"},
  "ks-quality-manuals-v2": {label: "내부 매뉴얼", kind: "manual"},
  "ks-quality-fabric-v2": {label: "Fabric", kind: "fabric"},
  "ks-quality-handovers-v2": {label: "교대 인수인계", kind: "document"},
  "ks-quality-workorders-v2": {label: "작업지시서", kind: "document"},
  "ks-quality-workiq-v2": {label: "Work IQ", kind: "work"}
};

export function sourceInfo(name) {
  return Object.hasOwn(sources, name) ? sources[name] : {label: name || "출처 미연결", kind: "unknown"};
}

function publicUrl(value) {
  if (typeof value !== "string" || !/^https?:\/\//i.test(value)) return null;
  try {
    const url = new URL(value);
    return !url.username && !url.password ? url.href : null;
  } catch {
    return null;
  }
}

export function indexReferences(references = []) {
  const index = new Map();
  for (const [position, ref] of references.entries()) {
    if (!ref || !["string", "number"].includes(typeof ref.id)) continue;
    const id = String(ref.id);
    if (index.has(id)) {
      index.set(id, null);
      continue;
    }
    index.set(id, {
      ...ref, id, anchor: `evidence-${position}`, ...sourceInfo(ref.source),
      title: typeof ref.title === "string" && ref.title.trim() ? ref.title : null,
      url: publicUrl(ref.citationUrl) || publicUrl(ref.url)
    });
  }
  return index;
}

export function referenceContent(ref) {
  if (ref.sourceContentStatus === "available" && typeof ref.sourcePreview === "string") {
    return {
      text: ref.sourcePreview,
      label: ref.sourceContentFormat === "json" ? "조회에 반환된 구조화 데이터" : "조회에 반환된 본문",
      field: ref.sourceContentField,
      truncated: !!ref.previewTruncated,
      limit: ref.sourcePreviewLimit,
      total: ref.sourceContentLength
    };
  }
  return {
    text: null,
    label: ref.sourceContentStatus === "missing"
      ? "API가 이 근거의 sourceData 본문을 제공하지 않았습니다."
      : ref.sourceContentStatus === "unavailable"
        ? "반환값에 읽을 수 있는 본문 필드가 없습니다. 메타데이터를 본문으로 대신 표시하지 않습니다."
        : "이전 응답에는 본문 추출 정보가 없습니다. 새로 질문해 조회 본문을 확인하세요."
  };
}

export function renderReferences(container, references, ids) {
  const open = new Set([...container.querySelectorAll("details[open]")].map(item => item.id));
  container.replaceChildren();
  if (!ids.length) {
    container.append(node("p", "답변에 인용된 근거가 아직 없습니다.", "small"));
    return;
  }
  for (const id of ids) {
    const ref = references.get(id);
    if (!ref) {
      container.append(node("p", `근거 미확인 · ${id} — 반환 reference와 연결되지 않습니다.`, "reference-missing"));
      continue;
    }
    const card = node("details", undefined, `reference-card source-${ref.kind}`);
    card.id = ref.anchor;
    card.open = open.has(card.id);
    const summary = node("summary");
    summary.append(node("span", `${ref.label} · ${id}`, `source-label source-${ref.kind}`),
      node("span", ref.title || `${ref.label} 조회 결과`, "reference-title"));
    card.append(summary);
    card.append(node("p", `${ref.source || "소스 미연결"} · 조회 활동 ${ref.activitySource ?? "미제공"} · [ref_id:${id}]`, "small"));
    const content = referenceContent(ref);
    card.append(node("h4", content.label, "reference-content-heading"));
    if (content.text !== null) {
      card.append(node("p", content.text, "reference-preview"));
      card.append(node("p", `${content.field || "본문"} · 반환 본문 ${content.total ?? "미제공"}자`, "small"));
      if (content.truncated) card.append(node("p", `본문이 길어 처음 ${content.limit}자만 표시합니다.`, "small"));
    }
    if (ref.sourceMetadata && Object.keys(ref.sourceMetadata).length) {
      const metadata = node("details", undefined, "reference-metadata");
      metadata.append(node("summary", "문서 식별자 · 메타데이터"), node("pre", JSON.stringify(ref.sourceMetadata, null, 2)));
      card.append(metadata);
    }
    if (ref.url) {
      const link = node("a", "원문 열기 ↗", "reference-link");
      link.href = ref.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      card.append(link);
    } else {
      card.append(node("p", "API가 직접 열 수 있는 원문 URL을 제공하지 않았습니다.", "small"));
    }
    container.append(card);
  }
}
