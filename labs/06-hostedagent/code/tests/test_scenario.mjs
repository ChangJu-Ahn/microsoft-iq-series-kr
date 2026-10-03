import test from "node:test";
import assert from "node:assert/strict";
import {renderScenario, scenarioLink} from "../static/scenario-render.js";

test("preserves scenario text, tables and headings while exposing section navigation", () => {
  const output = renderScenario("# 고객 브리프\n\n> 가상 고객입니다.\n\n## 1. 고객 상황\n\n**확인 사실**\n\n| 역할 | 데이터 |\n| --- | --- |\n| 품질 | QMS |\n\n## 2. 완료 기준\n\n미확인을 숨기지 않습니다.");
  assert.equal(output.sections.length, 2);
  assert.equal(output.sections[0].title, "1. 고객 상황");
  assert.match(output.html, /고객 브리프/);
  assert.match(output.html, /가상 고객입니다/);
  assert.match(output.html, /<table>/);
  assert.match(output.html, /미확인을 숨기지 않습니다/);
  assert.match(output.html, /id="scenario-section-1"/);
});

test("rewrites source-relative workshop links to the correct GitHub paths", () => {
  assert.equal(scenarioLink("../01-inhouse-system/README.md"),
    "https://github.com/ChangJu-Ahn/microsoft-iq-series-kr/blob/main/labs/01-inhouse-system/README.md");
  assert.equal(scenarioLink("../../README.md"),
    "https://github.com/ChangJu-Ahn/microsoft-iq-series-kr/blob/main/README.md");
});

test("serves existing diagrams locally but never loads arbitrary remote images", () => {
  const output = renderScenario("![기존 도식](assets/customer-problem.svg)\n\n![외부 이미지](https://example.com/track.png)");
  assert.match(output.html, /src="\/scenario\/assets\/customer-problem.svg"/);
  assert.match(output.html, /alt="기존 도식"/);
  assert.doesNotMatch(output.html, /src="https:\/\/example.com/);
});

test("keeps editable diagram sources as repository links", () => {
  assert.equal(scenarioLink("assets/customer-problem.excalidraw"),
    "https://github.com/ChangJu-Ahn/microsoft-iq-series-kr/blob/main/labs/00-getting-started/assets/customer-problem.excalidraw");
});

test("untrusted markup and unsafe schemes do not become executable content", () => {
  const output = renderScenario('<script>alert(1)</script>\n\n[unsafe](javascript:alert(1))');
  assert.doesNotMatch(output.html, /<script\b/);
  assert.doesNotMatch(output.html, /href="javascript:/);
  assert.equal(scenarioLink("file:///etc/passwd"), null);
  assert.equal(scenarioLink("//example.com"), null);
});
