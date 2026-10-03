import {node} from "./trace.js";

export function comparisonRows(history, kb, question) {
  return history.filter(row => row.kb === kb && row.question.trim() === question.trim()).reverse();
}

export function renderComparison(container, history, kb, question) {
  container.replaceChildren();
  const rows = comparisonRows(history, kb, question);
  if (!rows.length) {
    container.append(node("p", "동일 KB·동일 질문을 Low와 Medium으로 각각 실행하면 비교 결과가 여기에 표시됩니다.", "small"));
    return;
  }
  const table = node("table", undefined, "comparison-table");
  const head = node("thead");
  const labels = node("tr");
  for (const label of ["요청 강도", "계획", "검색", "추가 호출", "KB(초)", "생성(초)", "첫 답변·Agent(초)", "전체·Agent(초)", "전체·브라우저(초)", "응답·인용 검사"]) {
    labels.append(node("th", label));
  }
  head.append(labels);
  table.append(head);
  const body = node("tbody");
  const seconds = value => Number.isFinite(value) ? value.toFixed(3) : "미제공";
  for (const row of rows) {
    const tr = node("tr");
    for (const value of [
      row.reasoning_effort, row.trace_metrics.planning_passes, row.trace_metrics.search_calls,
      row.trace_metrics.additional_source_calls, seconds(row.retrieval_seconds),
      seconds(row.generation_seconds), seconds(row.first_delta_seconds),
      seconds(row.elapsed_seconds), seconds(row.client_elapsed_seconds),
      row.evidence.passed ? "통과" : "부분 확인"
    ]) tr.append(node("td", value));
    body.append(tr);
  }
  table.append(body);
  container.append(table);
}
