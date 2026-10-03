import {node} from "./dom.js";
import {sourceInfo, referenceContent} from "./references.js";
export {node} from "./dom.js";

function details(title, value) {
  const element = node("details");
  element.append(node("summary", title), node("pre", JSON.stringify(value, null, 2)));
  return element;
}

const queryFields = ["search", "query", "queryText", "searchText", "text"];
const asText = value => value == null ? "미제공" : typeof value === "string" ? value : JSON.stringify(value);

export function summarizeQuery(row) {
  const queries = [];
  const filters = [];
  const tools = [];
  for (const value of Object.values(row.arguments || {})) {
    if (!value || typeof value !== "object") continue;
    let input = value.toolArguments ?? value;
    if (value.toolName) tools.push(String(value.toolName));
    if (typeof input === "string") {
      try { input = JSON.parse(input); }
      catch { queries.push("도구 입력 해석 불가 — 상세 JSON 확인"); continue; }
    }
    if (!input || typeof input !== "object") continue;
    const query = queryFields.map(key => input[key]).find(text => typeof text === "string" && text.trim());
    if (query) queries.push(query);
    else if (value.toolName) {
      const inputs = Object.entries(input).map(([key, item]) => `${key}=${asText(item)}`).join(", ");
      queries.push(`${value.toolName}(${inputs})`);
    }
    if (input.filter != null) filters.push(asText(input.filter));
    if (value !== input && value.filter != null) filters.push(asText(value.filter));
  }
  return {
    id: row.id, source: row.source, count: row.count ?? "미제공",
    query: [...new Set(queries)].join("\n") || "검색문 미제공 — 상세 JSON 확인",
    filter: [...new Set(filters)].join("\n") || "미제공",
    tool: [...new Set(tools)].join(", ") || "미제공",
    warning: row.warning ? asText(row.warning.message ?? row.warning) : null,
    error: row.error ? asText(row.error.message ?? row.error) : null
  };
}

export function summarizeRepeat(row, queries) {
  return {
    previous: summarizeQuery(queries.find(query => String(query.id) === String(row.previousId)) || {id: row.previousId}),
    current: summarizeQuery(queries.find(query => String(query.id) === String(row.id)) || {id: row.id}),
    reason: row.reason || "추가 조회 이유는 응답에 명시되지 않았습니다."
  };
}

export function executionPasses(timeline) {
  const passes = [];
  let current = null;
  let number = 0;
  for (const activity of timeline) {
    if (activity.type === "modelQueryPlanning") {
      current = {number: ++number, planning: activity, activities: []};
      passes.push(current);
    } else {
      if (!current) {
        current = {number: null, planning: null, activities: []};
        passes.push(current);
      }
      current.activities.push(activity);
    }
  }
  return passes;
}

export function modelTokenCount(timeline) {
  const counts = timeline.filter(row => ["modelQueryPlanning", "modelAnswerSynthesis"].includes(row.type))
    .flatMap(row => [row.details?.inputTokens, row.details?.outputTokens]).filter(Number.isFinite);
  return counts.length ? counts.reduce((total, value) => total + value, 0) : null;
}

function queryBody(row) {
  const body = node("div", undefined, "query-body");
  body.append(node("p", row.query, "query-text"));
  const fields = node("dl", undefined, "query-fields");
  for (const [label, value] of [["도구", row.tool], ["필터", row.filter], ["관련 결과", row.count]]) {
    fields.append(node("dt", label), node("dd", value));
  }
  body.append(fields);
  if (row.warning) body.append(node("p", `경고: ${row.warning}`, "query-warning"));
  if (row.error) body.append(node("p", `오류: ${row.error}`, "query-error"));
  return body;
}

function stageMetrics(row) {
  const values = [];
  if (Number.isFinite(row.durationMs)) values.push(`${(row.durationMs / 1000).toFixed(3)}초`);
  if (Number.isFinite(row.details?.inputTokens)) values.push(`입력 ${row.details.inputTokens.toLocaleString()} 토큰`);
  if (Number.isFinite(row.details?.outputTokens)) values.push(`출력 ${row.details.outputTokens.toLocaleString()} 토큰`);
  if (Number.isFinite(row.details?.reasoningTokens)) values.push(`추론 ${row.details.reasoningTokens.toLocaleString()} 토큰`);
  return values.length ? values.join(" · ") : "시간·토큰 미제공";
}

function modelStage(row) {
  const names = {
    modelQueryPlanning: ["쿼리 계획", "질문을 해석하고 조회할 지식원·검색 입력을 준비하는 활동입니다."],
    modelAnswerSynthesis: ["KB 답변 합성", "조회한 근거를 바탕으로 Foundry IQ가 답변을 구성하는 활동입니다."],
    agenticReasoning: ["검색 추론 기록", "API가 반환한 검색 추론 강도와 토큰 정보를 표시합니다."]
  };
  const [title, description] = names[row.type] || [row.type, "이 활동의 반환값은 아래 근거에서 확인할 수 있습니다."];
  const stage = node("article", undefined, "execution-stage model-stage");
  const header = node("div", undefined, "execution-stage-heading");
  header.append(node("h4", title), node("span", stageMetrics(row), "stage-metrics"));
  stage.append(header, node("p", description, "stage-description"));
  if (row.type === "agenticReasoning") {
    stage.append(node("p",
      `검색 추론 강도: ${row.details?.retrievalReasoningEffort?.kind ?? "미제공"} · 논리 추론 강도: ${row.details?.logicalReasoningEffort?.kind ?? "미제공"}`,
      "small"));
  }
  if (row.details?.model?.modelName) stage.append(node("p", `모델: ${row.details.model.modelName}`, "small"));
  stage.append(details(`근거 · 활동 ${row.id} 반환 JSON`, row.details || row));
  return stage;
}

function searchStage(activity, query) {
  const info = sourceInfo(query.source);
  const stage = node("article", undefined, `execution-stage query-card source-border-${info.kind}`);
  const header = node("div", undefined, "execution-stage-heading");
  header.append(node("h4", `${info.label} · 활동 ${query.id}`),
    node("span", `관련 결과 ${query.count ?? "미제공"}건 · ${stageMetrics(activity)}`, "stage-metrics"));
  stage.append(header, queryBody(summarizeQuery(query)),
    details(`근거 · 활동 ${query.id} 반환 JSON`, activity.details || query));
  return stage;
}

export function renderTrace(container, trace) {
  container.replaceChildren();
  container.append(node("p",
    `요청 강도: ${trace.requested_reasoning_effort ?? "미제공"} · API 보고 강도: ${trace.observed_reasoning_efforts?.join(", ") || "미제공"} · KB 조회: ${trace.retrieval_seconds ?? "미제공"}초`,
    "small"));
  if (!trace.available) {
    container.append(node("p", "activity가 반환되지 않았습니다. 실행 단계나 검색 루프를 추측하지 않습니다."));
    return;
  }
  const metrics = node("div", undefined, "trace-metrics");
  for (const [label, key] of [
    ["계획 패스", "planning_passes"], ["검색·도구 호출", "search_calls"],
    ["동일 소스 추가 호출", "additional_source_calls"], ["KB 답변 합성", "synthesis_passes"],
    ["반환 근거", "reference_count"]
  ]) {
    const card = node("div");
    card.append(node("strong", trace.metrics[key]), node("span", label));
    metrics.append(card);
  }
  const tokens = node("div");
  tokens.append(node("strong", modelTokenCount(trace.timeline)?.toLocaleString() ?? "미제공"),
    node("span", "계획·합성 I/O 토큰"));
  metrics.append(tokens);
  container.append(metrics);
  container.append(node("p", "Foundry IQ의 관찰 가능한 실행 기록입니다. 내부 추론 전문이 아닙니다. 계획 패스 수 ≠ 재검색 횟수이며, 동일 소스의 추가 호출에는 병렬 하위 검색도 포함됩니다. 응답에 없는 재조회 이유는 추측하지 않습니다.", "small"));
  container.append(node("h3", "1. 실행 타임라인"));
  const wrapper = node("div", undefined, "table-scroll");
  const table = node("table");
  const header = node("tr");
  for (const label of ["ID", "활동 / 소스", "소요 시간", "관련 결과"]) header.append(node("th", label));
  const head = node("thead");
  head.append(header);
  table.append(head);
  const body = node("tbody");
  for (const row of trace.timeline) {
    const line = node("tr");
    for (const value of [row.id, `${row.type}\n${row.source || "모델/계획 활동"}`,
      row.durationMs == null ? "미제공" : `${row.durationMs} ms`, row.count ?? "미제공"]) {
      line.append(node("td", value));
    }
    body.append(line);
  }
  table.append(body);
  wrapper.append(table);
  container.append(wrapper);
  container.append(details("활동별 시작·종료 시각, 계획/생성 토큰, 상세 필드", trace.timeline));
  container.append(node("h3", "2. 계획 → 검색 → 답변 합성"));
  container.append(node("p", "반환 활동의 시간순으로 계획 패스를 묶었습니다. 서버가 제공한 반복 ID가 아니며, 묶음만으로 병렬 활동의 인과관계를 확정하지 않습니다.", "small"));
  const shown = new Set();
  for (const pass of executionPasses(trace.timeline)) {
    const card = node("section", undefined, "execution-pass");
    const header = node("div", undefined, "execution-pass-heading");
    header.append(node("span", pass.number ?? "—", "execution-pass-number"),
      node("h4", pass.number ? `${pass.number}차 계획·조회` : "계획 연결 미제공 활동"),
      node("span", `소스 호출 ${pass.activities.filter(row => row.source).length}회`, "stage-metrics"));
    card.append(header);
    if (pass.planning) card.append(modelStage(pass.planning));
    for (const activity of pass.activities) {
      const query = trace.queries.find(row => String(row.id) === String(activity.id));
      if (query) {
        shown.add(String(query.id));
        card.append(searchStage(activity, query));
      } else {
        card.append(modelStage(activity));
      }
    }
    container.append(card);
  }
  for (const query of trace.queries.filter(row => !shown.has(String(row.id)))) {
    container.append(searchStage({}, query));
  }
  if (!trace.queries.length) container.append(node("p", "반환된 소스 조회 활동이 없습니다."));
  container.append(node("p", "count는 관련성 기준을 통과한 결과 수입니다. 원본의 전체 건수나 최종 인용 수와 다릅니다.", "small"));
  container.append(node("h3", "3. 동일 소스 추가 호출"));
  if (!trace.repeatedQueries.length) container.append(node("p", "동일 소스 추가 호출 없음"));
  for (const row of trace.repeatedQueries) {
    const data = summarizeRepeat(row, trace.queries);
    const card = node("article", undefined, "query-card repeat-card");
    card.append(node("h4", `${sourceInfo(row.source).label} · 활동 ${row.previousId} → ${row.id}`),
      node("p", `${row.argumentsChanged ? "입력 변경" : "동일 입력"} · 관련 결과 ${row.previousCount ?? "미제공"} → ${row.count ?? "미제공"}`, "repeat-result"));
    const pair = node("div", undefined, "query-pair");
    for (const [label, item] of [["이전 조회", data.previous], ["후속 조회", data.current]]) {
      const section = node("section");
      section.append(node("h5", `${label} · 활동 ${item.id}`), queryBody(item));
      pair.append(section);
    }
    card.append(pair, node("p", data.reason, "small"), details("근거 · 이전/후속 조회 JSON", {
      ...row,
      previousQuery: trace.queries.find(query => String(query.id) === String(row.previousId)) ?? null,
      currentQuery: trace.queries.find(query => String(query.id) === String(row.id)) ?? null
    }));
    container.append(card);
  }
  container.append(details("시간이 겹치는 활동 ID 쌍 (관찰값, 인과관계 아님)", trace.overlaps));
  container.append(node("h3", "4. 조회 활동 → 근거 → KB 답변 인용"));
  for (const ref of trace.references) {
    const card = node("article", undefined, "query-card");
    const content = referenceContent(ref);
    card.append(node("h4", `${sourceInfo(ref.source).label} · 활동 ${ref.activitySource} → 근거 ${ref.id}`),
      node("p", ref.title || ref.docKey || "제목 미제공", "query-text"),
      node("p", `${ref.cited ? "KB 답변에 인용" : "KB 답변 인용 없음"} · [ref_id:${ref.id}]`, "small"),
      node("p", content.text ?? content.label, "reference-preview"));
    if (content.truncated) card.append(node("p", `본문 중 처음 ${content.limit}자 표시`, "small"));
    card.append(details("근거 · reference 반환 JSON", ref));
    container.append(card);
  }
  container.append(node("p", `미해결 KB 인용: ${trace.unresolvedCitations.join(", ") || "없음"}. 본문은 reference에 반환된 텍스트 필드이며 문서 전체나 모델이 사용한 정확한 문장 범위를 뜻하지 않습니다. 길이 제한은 해당 근거에 별도로 표시합니다.`, "small"));
}
