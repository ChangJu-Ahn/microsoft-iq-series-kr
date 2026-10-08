export const tourSteps = [
  {
    target: "#demo-mail-link", title: "아웃룩 이메일에서 업무 맥락 보기",
    text: "강조된 버튼을 눌러 메일을 열어 보세요. 목록의 각 메일을 클릭하면 본문 전체가 나옵니다. Work IQ가 찾는 요청·논의·담당자와 운영 데이터의 역할 차이를 확인합니다."
  },
  {
    target: "#demo-foundry-link", title: "Foundry IQ의 두 KB 설정 보기",
    text: "공정·품질 KB를 전환하고 연결된 KS의 설명과 검색·답변 지시문을 펼쳐 보세요. 여기서 KB는 여러 원본을 선택·조회해 근거를 조합하는 역할을 합니다."
  },
  {
    target: "#demo-fabric-link", title: "Fabric IQ의 온톨로지 살펴보기",
    text: "같은 온톨로지의 구버전·신버전을 전환해 보세요. 로트·설비·검사·부적합의 관계를 펼친 상태로 볼 수 있습니다. 캡처이므로 그래프 편집이나 실시간 조회는 하지 않습니다."
  },
  {
    target: "#demo-mes-link", title: "MES 목업에서 생산 원장 보기",
    text: "기존 외부 공개 MES 목업을 새 탭으로 엽니다. 로트 상태·공정·설비·생산 이력을 살펴보세요. 이 버튼은 외부 목업에 실제 접속하며, 기록된 답변 재생과는 별개입니다."
  },
  {
    target: "#kb", title: "조회할 Knowledge Base 선택",
    text: "공정 KB는 MES·매뉴얼·Web IQ의 3개 KS, 품질 KB는 Fabric·Work IQ·작업지시서·인수인계서의 4개 KS를 연결합니다. 원하는 KB를 고르거나 현재 선택을 유지하세요. 연결도와 오른쪽 설명도 함께 바뀝니다."
  },
  {
    target: "#question-entry", title: "업무 질문 선택",
    text: "‘데모 질문 4개 보기’를 눌러 전문을 읽고 ‘이 질문 사용’을 선택하세요. KB별 2개 질문을 준비했습니다. 클릭스루는 기록된 질문을 사용하며 자유 입력은 리얼 데모에서 가능합니다."
  },
  {
    target: "#send", title: "기록된 응답 재생",
    text: "강조된 ‘기록된 응답 재생’을 직접 눌러 보세요. 저장된 실제 응답이 순서대로 나타납니다. 새 검색이나 모델 호출은 없고, 재생이 완료되면 다음 설명으로 이동합니다."
  },
  {
    target: "#sources", title: "여러 KS의 근거가 하나의 답변으로",
    text: "소스별 배지와 아래 답변을 함께 보세요. 공정은 3개, 품질은 4개 KS가 실제로 인용된 기록입니다. 문장 옆 출처 배지를 누르면 해당 검색 본문이 펼쳐집니다. 반환 근거 수와 최종 인용 수는 서로 다릅니다."
  },
  {
    target: ".debug-toggle", title: "Foundry IQ 실행 기록 열기",
    text: "체크박스를 켜면 같은 응답에서 파싱한 계획·검색·근거 연결을 볼 수 있습니다. 추가 API 호출이나 비용은 없습니다. ‘다음’을 누를 때도 기록 패널을 펼쳐 드립니다."
  },
  {
    target: '[data-tour="timeline"]', title: "계획 순서와 Fan-out 이해하기",
    text: "실행 타임라인과 아래 ‘계획 → 검색 → 답변 합성’을 비교하세요. Fan-out 배지는 조회의 시작·종료 시간이 겹친 활동을 표시합니다. 활동 ID는 실행 순서가 아니며, 동일 소스 추가 호출도 무조건 재검색 루프는 아닙니다."
  }
];

export function nextTourStep(index, replayState) {
  if (!Number.isInteger(index) || index < 0 || index >= tourSteps.length) throw new Error("잘못된 가이드 단계입니다.");
  if (!["idle", "running", "complete"].includes(replayState)) throw new Error("잘못된 재생 상태입니다.");
  return index >= 6 && replayState !== "complete" ? 6 : index + 1;
}

export function tourPlacement(target, panel, viewport) {
  const margin = 12;
  let left = target.right + 18;
  let top = target.top;
  if (viewport.width < 700) {
    left = (viewport.width - panel.width) / 2;
    top = viewport.height - panel.height - margin;
  } else if (left + panel.width > viewport.width - margin) {
    if (target.left - panel.width - 18 >= margin) {
      left = target.left - panel.width - 18;
    } else {
      left = target.left;
      top = target.bottom + 18;
      if (top + panel.height > viewport.height - margin) top = target.top - panel.height - 18;
    }
  }
  return {
    left: Math.max(margin, Math.min(left, viewport.width - panel.width - margin)),
    top: Math.max(margin, Math.min(top, viewport.height - panel.height - margin))
  };
}

export function initTour() {
  const $ = id => document.getElementById(id);
  const panel = $("demo-tour");
  const questionDialog = $("question-dialog");
  const storageKey = "iq-demo-tour-v1";
  let index = 0;
  let active = false;
  let replayState = "idle";
  let frame = null;
  let highlights = [];
  let returnFocus;

  function storageWarning(error) {
    console.warn("demo_tour_storage_unavailable", error);
    $("tour-announcement").textContent = "브라우저에 가이드 종료 상태를 저장할 수 없습니다. 다음 방문에 다시 표시될 수 있습니다.";
  }

  function clearHighlights() {
    for (const {element, describedBy} of highlights) {
      element.classList.remove("tour-highlight");
      if (describedBy === null) element.removeAttribute("aria-describedby");
      else element.setAttribute("aria-describedby", describedBy);
    }
    highlights = [];
  }

  function highlight(element) {
    if (!element) return;
    const describedBy = element.getAttribute("aria-describedby");
    highlights.push({element, describedBy});
    element.classList.add("tour-highlight");
    element.setAttribute("aria-describedby", [describedBy, "tour-description"].filter(Boolean).join(" "));
  }

  function position() {
    frame = null;
    if (!active || questionDialog.open) return;
    const target = document.querySelector(tourSteps[index].target);
    if (!target) return;
    const box = panel.getBoundingClientRect();
    const viewport = window.visualViewport;
    const placement = tourPlacement(target.getBoundingClientRect(), box, {
      width: viewport?.width ?? innerWidth, height: viewport?.height ?? innerHeight
    });
    panel.style.left = `${placement.left}px`;
    panel.style.top = `${placement.top}px`;
  }

  function schedulePosition() {
    if (active && frame === null) frame = requestAnimationFrame(position);
  }

  function close(completed = false) {
    active = false;
    panel.hidden = true;
    clearHighlights();
    document.body.classList.remove("tour-active");
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    $("tour-announcement").textContent = completed
      ? "가이드를 마쳤습니다. 다른 KB의 질문도 체험하거나 ‘10단계 가이드 다시 보기’로 돌아올 수 있습니다."
      : "가이드를 닫았습니다. 언제든 ‘10단계 가이드 다시 보기’로 시작할 수 있습니다.";
    try { localStorage.setItem(storageKey, "seen"); }
    catch (error) { storageWarning(error); }
    if (returnFocus?.isConnected && !returnFocus.disabled) returnFocus.focus({preventScroll: true});
    else $("tour-start").focus({preventScroll: true});
  }

  function showStep(next, focus = true) {
    if (next === tourSteps.length) {
      close(true);
      return;
    }
    index = next >= 7 && replayState !== "complete" ? 6 : next;
    clearHighlights();
    if (index === 9) {
      $("debug-toggle").checked = true;
      $("debug-toggle").dispatchEvent(new Event("change"));
    }
    const step = tourSteps[index];
    const target = document.querySelector(step.target);
    if (!target || !target.getClientRects().length) {
      close();
      $("tour-announcement").textContent = "안내할 화면을 찾지 못했습니다. 응답을 재생한 뒤 가이드를 다시 시작하세요.";
      console.warn("demo_tour_target_missing", step.target);
      return;
    }
    panel.hidden = questionDialog.open;
    $("tour-progress").textContent = `${index + 1} / ${tourSteps.length} · 직접 체험 가이드`;
    $("tour-title").textContent = step.title;
    $("tour-description").textContent = step.text;
    $("tour-prev").disabled = index === 0;
    $("tour-next").disabled = index === 6 && replayState !== "complete";
    $("tour-next").textContent = index === 9 ? "가이드 마치기 ✓" : "다음 →";
    $("tour-hint").textContent = index < 4
      ? "새 탭에서 둘러본 뒤 이 탭으로 돌아와 ‘다음’을 누르세요. 지금 열지 않고 넘어가도 됩니다."
      : index === 6
        ? replayState === "running" ? "재생 중입니다. 중지하면 다시 재생할 수 있습니다."
          : replayState === "complete" ? "현재 질문의 완성된 응답이 있습니다. 다음 단계로 이동할 수 있습니다."
            : "응답 재생 버튼을 눌러야 다음 단계로 이동합니다."
        : index === 9
          ? document.querySelector("#debug-content .fan-out-badge")
            ? "이 기록에는 시간이 겹친 조회가 있습니다. 아래 계획 패스도 스크롤해서 확인하세요. 현재 재생 속도가 아닌 기록 당시 측정값입니다."
            : "이 기록에는 Fan-out 배지가 없습니다. 배지가 없다는 이유만으로 직렬 실행이라고 단정하지 않습니다."
          : "강조된 화면에서 직접 선택해 보거나 ‘다음’으로 이동하세요.";
    if (!questionDialog.open) {
      highlight(target);
      if (index === 7) {
        highlight($("response"));
        highlight(document.querySelector("#answer .citation"));
      }
      if (index === 9) highlight(document.querySelector("#debug-content .execution-pass"));
      const top = target.getBoundingClientRect().top + scrollY - 60;
      window.scrollTo({top: Math.max(0, top), behavior: "instant"});
      position();
      if (focus) $("tour-title").focus({preventScroll: true});
    }
  }

  function start() {
    returnFocus = $("tour-start");
    active = true;
    document.body.classList.add("tour-active");
    $("tour-announcement").textContent = "";
    showStep(0);
  }

  $("tour-start").hidden = false;
  $("tour-start").onclick = start;
  $("tour-close").onclick = () => close();
  $("tour-prev").onclick = () => showStep(Math.max(0, index - 1));
  $("tour-next").onclick = () => showStep(nextTourStep(index, replayState));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && active && !questionDialog.open) {
      event.preventDefault();
      close();
    }
  });
  new MutationObserver(() => {
    if (!active) return;
    if (questionDialog.open) {
      panel.hidden = true;
      clearHighlights();
    } else showStep(index, false);
  }).observe(questionDialog, {attributes: true, attributeFilter: ["open"]});
  $("debug-toggle").addEventListener("change", () => {
    if (active && index === 9 && !$("debug-toggle").checked) showStep(8);
  });
  window.addEventListener("scroll", schedulePosition, {passive: true});
  window.addEventListener("resize", schedulePosition);
  window.visualViewport?.addEventListener("resize", schedulePosition);
  new ResizeObserver(schedulePosition).observe(panel);
  let seen = false;
  let storageError;
  try { seen = localStorage.getItem(storageKey) === "seen"; }
  catch (error) { storageError = error; }
  if (!seen) start();
  if (storageError) storageWarning(storageError);

  return {
    setReplayState(state) {
      nextTourStep(0, state);
      replayState = state;
      if (!active) return;
      if (index >= 7 && state !== "complete") showStep(6);
      else if (index === 6) showStep(state === "complete" ? 7 : 6);
    }
  };
}
