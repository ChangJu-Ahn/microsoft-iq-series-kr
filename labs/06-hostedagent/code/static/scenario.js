import {renderScenario} from "./scenario-render.js";
import {node} from "./dom.js";

const content = document.getElementById("scenario-content");
const toc = document.getElementById("scenario-toc");
try {
  const response = await fetch("/scenario/content");
  if (!response.ok) throw new Error(`시나리오 문서 조회 실패: HTTP ${response.status}`);
  const markdown = await response.text();
  if (!markdown.trim()) throw new Error("시나리오 문서가 비어 있습니다.");
  const rendered = renderScenario(markdown);
  content.innerHTML = rendered.html;
  toc.replaceChildren();
  for (const section of rendered.sections) {
    const link = node("a", section.title);
    link.href = "#" + section.id;
    toc.append(link);
  }
  content.setAttribute("aria-busy", "false");
} catch (error) {
  content.replaceChildren(node("p", error.message, "scenario-error"),
    node("p", "아래의 원본 README 링크로 내용을 확인하거나 잠시 후 새로고침하세요."));
  content.setAttribute("aria-busy", "false");
  toc.replaceChildren(node("p", "목차를 불러오지 못했습니다."));
}
