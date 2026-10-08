import {node} from "./dom.js";
import {loadDemo} from "./demo.js";

const $ = id => document.getElementById(id);
const isFabric = location.pathname.replace(/\/$/, "") === "/demo/fabric";
const choices = isFabric
  ? [["legacy", "구버전 · 펼쳐진 온톨로지 그래프"], ["new", "신버전 · 온톨로지 화면"]]
  : [["process", "공정 KB · 3개 KS"], ["quality", "품질 KB · 4개 KS"]];
let settings;
let catalogs;

function detail(title, text, open = false) {
  const block = node("details", undefined, "iq-detail");
  block.open = open;
  block.append(node("summary", title), node("p", text));
  return block;
}

function selectView(value) {
  if (!choices.some(([key]) => key === value)) throw new Error("등록되지 않은 참고 화면입니다.");
  const title = choices.find(([key]) => key === value)[1];
  const image = `/static/demo/${isFabric ? `fabric-${value}` : `foundry-${value}`}.png`;
  $("iq-error").textContent = "";
  $("iq-image").hidden = true;
  $("iq-image").alt = isFabric ? `${title} · 노드가 펼쳐진 배치를 고정한 실제 화면` : `${title} · 실제 Azure AI Search Knowledge Base 설정 화면`;
  $("iq-image").src = image;
  $("iq-dialog-image").src = image;
  $("iq-dialog-image").alt = $("iq-image").alt;
  $("iq-capture-title").textContent = title;
  $("iq-dialog-title").textContent = title;
  $("iq-capture-note").textContent = isFabric
    ? "같은 온톨로지 · 11개 엔터티 / 18개 관계 · 공유된 배치 그대로 고정 · 자동 재배치 없음"
    : `${settings[value].name} · 2026-10-08 설정 확인 · 계정 표시 제외`;
  $("iq-zoom").value = "fit";
  $("iq-image-viewport").className = "iq-image-viewport zoom-fit";
  $("iq-image-viewport").scrollTo(0, 0);
  for (const button of $("iq-view-options").querySelectorAll("button")) {
    button.setAttribute("aria-pressed", String(button.dataset.view === value));
  }
  const content = $("iq-details");
  content.replaceChildren();
  if (isFabric) {
    const fabric = settings.fabric;
    content.append(node("h2", "같은 온톨로지, 두 가지 화면"));
    content.append(node("p", value === "legacy"
      ? `공유된 구버전 그래프(${fabric.legacy_title})입니다. 원형 노드와 관계선이 서로 구분되도록 펼쳐 놓은 상태를 보존했습니다.`
      : `공유된 신버전 화면(${fabric.new_title})입니다. Inspection을 선택한 Full ontology 화면과 펼쳐진 카드 배치를 그대로 보존했습니다.`));
    const entities = node("div", undefined, "iq-entities");
    for (const name of fabric.entity_types) entities.append(node("span", name, "source source-fabric"));
    content.append(detail("엔터티 11개 · 관계 18개", "두 화면은 같은 온톨로지를 표현합니다. 데이터가 두 벌이라는 뜻이 아니며, 연결 관계를 다시 생성하거나 자동 배치하지 않습니다.", true), entities);
    content.append(detail("조작 범위", "위 버튼으로 구버전·신버전을 전환하고 확대해서 관계선을 확인합니다. 엔터티 수정·조회는 실행하지 않는 화면 기록입니다."));
  } else {
    const item = settings[value];
    const catalog = catalogs[value];
    content.append(node("h2", item.name), node("p", catalog.description));
    const metrics = node("dl", undefined, "iq-setting-summary");
    for (const [label, text] of [["Reasoning effort", item.reasoning_effort],
      ["Output mode", item.output_mode], ["Chat completion model", item.model]]) {
      metrics.append(node("dt", label), node("dd", text));
    }
    content.append(metrics, node("h3", `연결된 Knowledge Sources · ${item.sources.length}개`));
    for (const name of item.sources) {
      const source = catalog.sources.find(source => source.name === name);
      content.append(detail(`${name} · ${source.kind}`, source.description));
    }
    content.append(detail("Retrieval instructions · 검색 지시문 전문", item.retrieval_instructions, true),
      detail("Answer instructions · 답변 지시문 전문", item.answer_instructions, true));
  }
  const url = new URL(location.href);
  url.searchParams.set(isFabric ? "view" : "kb", value);
  history.replaceState(null, "", url);
}

$("iq-title").textContent = isFabric ? "Fabric IQ · 같은 온톨로지, 두 화면" : "Foundry IQ · 두 Knowledge Base의 설정";
document.title = `${isFabric ? "Fabric IQ" : "Foundry IQ"} 구성 · 클릭스루 데모`;
$("iq-description").textContent = isFabric
  ? "구버전 그래프와 신버전 온톨로지 화면을 전환해 보세요. 첫 화면부터 노드가 겹치지 않도록 펼쳐 놓은 배치를 유지합니다."
  : "실제 Azure AI Search 포털에 구성된 공정·품질 KB입니다. KB를 전환하고 연결된 KS의 역할과 검색·답변 지시문을 펼쳐 확인하세요.";
document.querySelector(`.top-nav a[href="/demo/${isFabric ? "fabric" : "foundry"}"]`).setAttribute("aria-current", "page");
$("iq-image").onload = () => {
  $("iq-image").hidden = false;
  $("iq-zoom").disabled = false;
  $("iq-focus").disabled = false;
};
$("iq-image").onerror = () => {
  $("iq-error").textContent = "기록 이미지를 불러오지 못했습니다. 배포 파일을 확인하거나 다른 화면을 선택하세요.";
  $("iq-image").hidden = true;
  $("iq-zoom").disabled = true;
  $("iq-focus").disabled = true;
};
$("iq-zoom").onchange = () => {
  $("iq-image-viewport").className = `iq-image-viewport zoom-${$("iq-zoom").value}`;
};
$("iq-focus").onclick = () => $("iq-image-dialog").showModal();
$("iq-dialog-close").onclick = () => $("iq-image-dialog").close();

try {
  const response = await fetch("/static/demo/iq-settings.json");
  if (!response.ok) throw new Error(`설정 기록 조회 실패: HTTP ${response.status}`);
  settings = await response.json();
  if (isFabric) {
    if (settings.fabric?.entity_types?.length !== 11 || settings.fabric.relationship_count !== 18) {
      throw new Error("온톨로지 기록의 엔터티·관계 정보가 올바르지 않습니다.");
    }
  } else {
    catalogs = (await loadDemo()).catalogs;
    for (const kb of ["process", "quality"]) {
      const item = settings[kb];
      if (!item || ["name", "reasoning_effort", "output_mode", "model", "retrieval_instructions", "answer_instructions"]
        .some(key => typeof item[key] !== "string" || !item[key].trim()) ||
        !Array.isArray(item.sources) || item.sources.length !== catalogs[kb].sources.length ||
        !catalogs[kb].sources.every(source => item.sources.includes(source.name))) {
        throw new Error("KB 설정 기록이 연결된 KS 목록과 일치하지 않습니다.");
      }
    }
  }
  for (const [key, label] of choices) {
    const button = node("button", label, "secondary");
    button.type = "button";
    button.dataset.view = key;
    button.onclick = () => selectView(key);
    $("iq-view-options").append(button);
  }
  const requested = new URLSearchParams(location.search).get(isFabric ? "view" : "kb");
  selectView(requested || choices[0][0]);
} catch (error) {
  $("iq-error").textContent = `참고 화면을 열지 못했습니다: ${error.message}`;
}
