import {readEvents} from "./sse.js";
import {renderTrace, node} from "./trace.js";
import {renderComparison} from "./comparison.js";
import {renderMarkdown} from "./markdown.js";
import {indexReferences, renderReferences, sourceInfo} from "./references.js";
import {questionChoices, questionFromSelection, matchingQuestion} from "./question-picker.js";

const $ = id => document.getElementById(id);
let csrf = "";
let questions = [];
let selectedSample = "";
let controller;
let catalogController;
const history = [];
const controls = ["kb", "reasoning-effort", "question", "sample", "send"];

function comparison() {
  renderComparison($("comparison-results"), history, $("kb").value, $("question").value);
}

function updateArchitecture() {
  const selected = $("kb").value;
  $("architecture-selection").textContent = selected === "process" ? "공정 KB 선택" : "품질 KB 선택";
  for (const branch of document.querySelectorAll(".architecture-branch")) {
    branch.classList.toggle("is-selected", branch.dataset.kb === selected);
  }
}

async function showCatalog() {
  catalogController?.abort();
  const current = new AbortController();
  catalogController = current;
  const selected = $("kb").value;
  const container = $("catalog-content");
  container.textContent = "KB와 연결된 KS 설명을 읽고 있습니다…";
  try {
    const data = await (await api(`/api/knowledge-base?kb=${encodeURIComponent(selected)}`,
      {signal: current.signal})).json();
    if (current.signal.aborted || selected !== $("kb").value) return;
    container.replaceChildren(node("h2", data.name), node("p", data.description || "등록된 KB 설명이 없습니다."));
    container.append(node("p", `KB 기본 추론 강도: ${data.default_reasoning_effort || "미설정"} · 질문 영역의 선택값이 요청 단위로 우선 적용됩니다.`, "small"));
    container.append(node("h3", `연결된 Knowledge Sources · ${data.sources.length}개`));
    for (const source of data.sources) {
      const card = node("article", undefined, "catalog-source");
      card.append(node("h3", source.name), node("span", source.kind, "source"),
        node("p", source.description || "등록된 KS 설명이 없습니다."));
      container.append(card);
    }
  } catch (error) {
    if (error.name !== "AbortError" && catalogController === current) {
      container.replaceChildren(node("p", error.message, "catalog-error"));
    }
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const data = await response.json();
    throw new Error(typeof data.detail === "string" ? data.detail : (data.detail?.message || `HTTP ${response.status}`));
  }
  return response;
}

function evidence(report) {
  $("sources").replaceChildren();
  for (const source of report.sources) {
    const item = document.createElement("span");
    const info = sourceInfo(source.name);
    item.className = `source source-${info.kind}` + (source.ok ? "" : " missing");
    item.title = source.name;
    item.textContent = `${source.ok ? "✓" : "!"} ${info.label} · 반환 근거 ${source.references} / 인용 ${source.cited}`;
    $("sources").append(item);
  }
}

function resetAnswer(message) {
  $("response").hidden = true;
  $("latency").hidden = true;
  $("sources").replaceChildren();
  $("answer-sources").replaceChildren();
  $("answer-sources-section").hidden = true;
  $("debug-content").textContent = "선택한 KB에 질문하면 실행 기록을 표시합니다.";
  $("status").className = "";
  $("status").textContent = message;
}

function refreshKnowledgeBase() {
  updateArchitecture();
  resetAnswer("KB가 변경되었습니다. 새 질문을 실행하세요.");
  showCatalog();
  comparison();
}

function populateQuestionChoices() {
  $("question-list").replaceChildren();
  const groups = new Map();
  for (const choice of questionChoices(questions)) {
    if (!groups.has(choice.kb)) {
      const group = node("section", undefined, "question-group");
      group.append(node("h3", choice.group));
      groups.set(choice.kb, group);
      $("question-list").append(group);
    }
    const card = node("article", undefined, "question-option");
    card.dataset.questionValue = choice.value;
    const button = node("button", "이 질문 사용", "secondary");
    button.type = "button";
    button.dataset.questionValue = choice.value;
    button.setAttribute("aria-label", `${choice.group} ${choice.label} 사용`);
    card.append(node("h4", choice.label), node("p", choice.question, "question-full-text"), button);
    groups.get(choice.kb).append(card);
  }
}

$("sample").onclick = () => {
  for (const card of $("question-list").querySelectorAll(".question-option")) {
    card.classList.toggle("is-selected", card.dataset.questionValue === selectedSample);
  }
  $("question-dialog").showModal();
};
$("close-question-dialog").onclick = () => $("question-dialog").close();
$("question-list").onclick = event => {
  const button = event.target.closest("button[data-question-value]");
  if (!button) return;
  try {
    const selected = questionFromSelection(questions, button.dataset.questionValue);
    selectedSample = button.dataset.questionValue;
    const changedKB = $("kb").value !== selected.kb;
    $("kb").value = selected.kb;
    $("question").value = selected.question;
    if (changedKB) refreshKnowledgeBase();
    else {
      resetAnswer("실습 질문을 선택했습니다. 수정하거나 조회를 실행하세요.");
      comparison();
    }
    $("sample-help").textContent = `05 실습 질문 ${Number(selectedSample) + 1}을 선택했습니다. 아래에서 자유롭게 수정할 수 있습니다.`;
    $("question-dialog").close();
    $("question").focus();
  } catch (error) {
    $("question-dialog-help").textContent = error.message;
  }
};

$("kb").onchange = () => {
  if (selectedSample !== "") {
    const first = questions.find(item => item.kb === $("kb").value);
    if (first) $("question").value = first.question;
  }
  selectedSample = matchingQuestion(questions, $("kb").value, $("question").value);
  $("sample-help").textContent = selectedSample === "" ? "직접 작성한 질문을 유지했습니다." : "선택한 Knowledge Base의 실습 질문입니다. 팝업에서 다른 질문을 고를 수 있습니다.";
  refreshKnowledgeBase();
};
$("question").oninput = () => {
  selectedSample = matchingQuestion(questions, $("kb").value, $("question").value);
  if (questions.length) $("sample-help").textContent = selectedSample === "" ? "직접 입력하거나 수정한 질문입니다." : "05 실습 질문과 같은 문장입니다. 자유롭게 수정할 수 있습니다.";
  comparison();
};
$("cancel").onclick = () => controller?.abort();
$("answer").onclick = event => {
  const citation = event.target.closest("a.citation");
  if (!citation) return;
  const card = document.getElementById(citation.getAttribute("href").slice(1));
  if (!card) return;
  event.preventDefault();
  card.open = true;
  card.scrollIntoView({block: "center"});
  card.querySelector("summary").focus({preventScroll: true});
};
$("debug-toggle").onchange = () => { $("debug-panel").hidden = !$("debug-toggle").checked; };
$("logout").onclick = async () => {
  try {
    controller?.abort();
    await api("/auth/logout", {method: "POST", headers: {"X-CSRF-Token": csrf}});
    location.reload();
  } catch (error) { $("page-error").textContent = error.message; }
};
$("question-form").onsubmit = async event => {
  event.preventDefault();
  const request = {kb: $("kb").value, question: $("question").value.trim(),
    reasoning_effort: $("reasoning-effort").value};
  const clientStarted = performance.now();
  let clientFirstDelta = null;
  let completion = null;
  let answerMarkdown = "";
  let renderFrame = null;
  let references = new Map();
  let citationKey = null;
  const renderAnswer = () => {
    $("answer").innerHTML = renderMarkdown(answerMarkdown, references);
    const ids = [...new Set([...$("answer").querySelectorAll(".citation[data-ref-id]")]
      .map(citation => citation.dataset.refId))];
    const nextKey = JSON.stringify(ids);
    if (nextKey !== citationKey) {
      renderReferences($("answer-sources"), references, ids);
      $("answer-sources-heading").textContent = `답변에 사용한 근거 · ${ids.length}개`;
      $("answer-sources-section").hidden = ids.length === 0;
      citationKey = nextKey;
    }
    renderFrame = null;
  };
  controller = new AbortController();
  for (const id of controls) $(id).disabled = true;
  $("cancel").hidden = false;
  $("answer").textContent = "";
  $("answer-sources").replaceChildren();
  $("answer-sources-section").hidden = true;
  $("sources").replaceChildren();
  $("debug-content").textContent = "Foundry IQ 실행 기록을 기다리고 있습니다.";
  $("response").hidden = false;
  $("latency").hidden = true;
  $("status").className = "";
  $("status").textContent = "Hosted Agent에 연결합니다…";
  let completed = false;
  try {
    const response = await api("/api/chat", {
      method: "POST", signal: controller.signal,
      headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf},
      body: JSON.stringify(request),
    });
    for await (const {name, data} of readEvents(response.body)) {
      if (name === "status") $("status").textContent = data.message;
      if (name === "evidence") evidence(data);
      if (name === "trace") {
        references = indexReferences(data.references);
        citationKey = null;
        renderTrace($("debug-content"), data);
        if (answerMarkdown) renderAnswer();
      }
      if (name === "delta") {
        clientFirstDelta ??= (performance.now() - clientStarted) / 1000;
        answerMarkdown += data.text;
        if (renderFrame === null) renderFrame = requestAnimationFrame(renderAnswer);
      }
      if (name === "error") throw new Error(`${data.message} (${data.code})`);
      if (name === "done") {
        if (data.reasoning_effort !== request.reasoning_effort || !Number.isFinite(data.retrieval_seconds)) {
          throw new Error("Agent의 추론 강도·시간 정보가 요청과 맞지 않습니다. 배포 버전을 확인하세요.");
        }
        completion = data;
        completed = true;
        evidence(data.evidence);
        $("status").textContent = `${data.reasoning_effort} · ${data.evidence.passed ? "전체 소스 응답·인용 확인 (업무 내용은 별도 검토)" : "부분 확인 · 누락/오류/인용을 확인하세요"} · ${data.elapsed_seconds}초 · ${data.delta_count}개 실시간 delta`;
        if (!data.evidence.passed) $("status").className = "error";
      }
    }
    if (!completed) throw new Error("완료 이벤트 없이 연결이 종료됐습니다. 답변은 미완료입니다.");
    const clientElapsed = (performance.now() - clientStarted) / 1000;
    history.push({...request, ...completion, client_elapsed_seconds: clientElapsed});
    if (history.length > 10) history.shift();
    comparison();
    $("latency").textContent = `KB 조회 ${completion.retrieval_seconds}초 · 모델 생성 ${completion.generation_seconds}초 · 첫 답변(Agent) ${completion.first_delta_seconds}초 · 전체(Agent) ${completion.elapsed_seconds}초 · 첫 답변(브라우저) ${clientFirstDelta?.toFixed(3) ?? "미수신"}초 · 전체(브라우저) ${clientElapsed.toFixed(3)}초`;
    $("latency").hidden = false;
  } catch (error) {
    $("status").className = "error";
    $("status").textContent = error.name === "AbortError" ? "사용자가 중지했습니다. 답변은 미완료입니다." : error.message;
  } finally {
    if (renderFrame !== null) cancelAnimationFrame(renderFrame);
    renderAnswer();
    for (const id of controls) $(id).disabled = false;
    $("cancel").hidden = true;
    controller = null;
  }
};

try {
  const response = await fetch("/api/me");
  if (response.status !== 401) {
    if (!response.ok) throw new Error(`세션 확인 실패: HTTP ${response.status}`);
    const user = await response.json();
    csrf = user.csrf;
    $("user").textContent = user.name;
    $("login-panel").hidden = true;
    $("chat-panel").hidden = false;
    updateArchitecture();
    showCatalog();
    try {
      questions = await (await api("/api/questions")).json();
      populateQuestionChoices();
      if (!$("question").value.trim()) {
        const first = questions.find(item => item.kb === $("kb").value);
        if (first) $("question").value = first.question;
      }
      selectedSample = matchingQuestion(questions, $("kb").value, $("question").value);
      $("sample-help").textContent = `직접 입력하거나 ‘05 실습 질문 보기’에서 ${questions.length}개 질문의 전문을 읽고 선택하세요.`;
      comparison();
    } catch (error) {
      $("sample-help").textContent = `실습 질문 목록을 불러오지 못했습니다: ${error.message} 직접 입력은 계속 사용할 수 있습니다.`;
      $("question-list").replaceChildren(node("p", `질문 목록 조회 실패: ${error.message}`, "catalog-error"));
    }
  }
} catch (error) { $("page-error").textContent = error.message; }
