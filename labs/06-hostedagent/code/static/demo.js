export function validateDemo(data) {
  const invalid = () => { throw new Error("데모 기록이 올바르지 않거나 완전하지 않습니다. 배포 파일을 확인하세요."); };
  if (data?.schema_version !== 1 || !Array.isArray(data.cases) || data.cases.length !== 4) invalid();
  for (const kb of ["process", "quality"]) {
    if (data.cases.filter(item => item.kb === kb).length !== 2 ||
        !data.catalogs?.[kb]?.name || !Array.isArray(data.catalogs[kb].sources) ||
        data.catalogs[kb].sources.length !== (kb === "process" ? 3 : 4)) invalid();
  }
  const questions = new Set();
  for (const item of data.cases) {
    if (typeof item.question !== "string" || !item.question.trim() || item.reasoning_effort !== "medium" ||
        !Number.isFinite(Date.parse(item.recorded_at)) || !Array.isArray(item.events)) invalid();
    const key = `${item.kb}:${item.question}`;
    if (questions.has(key)) invalid();
    questions.add(key);
    const events = item.events;
    if (events.some(event => !["status", "evidence", "trace", "delta", "done"].includes(event.name) || !event.data) ||
        events.filter(event => event.name === "done").length !== 1 ||
        events.at(-1)?.name !== "done" ||
        !events.some(event => event.name === "trace" && Array.isArray(event.data.references)) ||
        !events.some(event => event.name === "delta" && typeof event.data.text === "string")) invalid();
    const completion = events.at(-1).data;
    if (completion.reasoning_effort !== item.reasoning_effort ||
        !Number.isFinite(completion.retrieval_seconds) || !completion.evidence?.sources ||
        !completion.trace_metrics) invalid();
    const report = completion.evidence;
    const expected = data.catalogs[item.kb].sources.map(source => source.name);
    const references = events.find(event => event.name === "trace").data.references;
    const answer = events.filter(event => event.name === "delta").map(event => event.data.text).join("");
    const cited = new Set([...answer.matchAll(/\[ref_id:([^\]]+)\]/g)].map(match => match[1]));
    if (report.passed !== true || !Array.isArray(report.sources) || report.sources.length !== expected.length ||
        !expected.every(name => report.sources.some(source =>
          source.name === name && source.ok && source.references > 0 && source.cited > 0) &&
          references.some(ref => ref.source === name && cited.has(String(ref.id))))) {
      throw new Error("모든 KS의 반환 근거와 최종 답변 인용이 확인된 데모 기록만 사용할 수 있습니다.");
    }
  }
  return data;
}

export async function loadDemo() {
  const response = await fetch("/static/demo/recordings.json");
  if (!response.ok) throw new Error(`데모 기록을 불러오지 못했습니다: HTTP ${response.status}`);
  return validateDemo(await response.json());
}

export function recordingFor(data, request) {
  const record = data.cases.find(item => item.kb === request.kb &&
    item.question.trim() === request.question.trim() && item.reasoning_effort === request.reasoning_effort);
  if (!record) throw new Error("기록된 질문과 Medium 모드만 재생할 수 있습니다. 데모 질문 목록에서 선택하세요.");
  return record;
}

function pause(milliseconds, signal) {
  signal.throwIfAborted();
  return new Promise((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(signal.reason);
    };
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve();
    }, milliseconds);
    signal.addEventListener("abort", abort, {once: true});
  });
}

export async function* replay(record, signal) {
  for (const event of record.events) {
    signal.throwIfAborted();
    await pause(event.name === "delta" ? 12 : 180, signal);
    yield structuredClone(event);
  }
}
