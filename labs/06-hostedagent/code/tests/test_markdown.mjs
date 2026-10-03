import test from "node:test";
import assert from "node:assert/strict";
import {renderMarkdown} from "../static/markdown.js";

test("renders Korean headings, emphasis, lists and citations", () => {
  const html = renderMarkdown("## 확인된 사실\n\n**상태**와 `LOT0012`\n\n- 항목 [ref_id:0]\n- 다음 항목\n\n1. 점검\n2. 확인");
  for (const text of ["<h2>확인된 사실</h2>", "<strong>상태</strong>", "<code>LOT0012</code>", "<ul>", "<ol>", "[ref_id:0]"]) {
    assert.ok(html.includes(text), text);
  }
});

test("renders tables, blockquotes, horizontal rules and fenced code", () => {
  const html = renderMarkdown("| 소스 | 결과 |\n| --- | --- |\n| MES | 확인 |\n\n> 추가 확인\n\n---\n\n```python\nprint('<x>')\n```");
  for (const text of ["<table>", "<th>소스</th>", "<td>MES</td>", "<blockquote>", "<hr>", "<pre><code", "&lt;x&gt;"]) {
    assert.ok(html.includes(text), text);
  }
});

test("escapes raw HTML and cannot execute model-provided elements", () => {
  const html = renderMarkdown('<script>alert(1)</script>\n\n<img src=x onerror="alert(1)">\n\n<svg onload=alert(1)>');
  assert.doesNotMatch(html, /<(script|img|svg|iframe|style)\b/i);
  assert.match(html, /&lt;script&gt;/);
});

test("blocks unsafe links including entity-encoded protocols", () => {
  for (const destination of ["javascript:alert(1)", "vbscript:msgbox(1)", "data:text/html,x",
    "file:///etc/passwd", "javascript&#x3A;alert(1)", "//example.com", "/auth/logout"]) {
    assert.doesNotMatch(renderMarkdown(`[link](${destination})`), /<a\b/i, destination);
  }
});

test("preserves public source links with safe new-tab attributes", () => {
  const html = renderMarkdown("[문서](https://learn.microsoft.com/azure/search/)");
  assert.match(html, /href="https:\/\/learn.microsoft.com\/azure\/search\/"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /rel="noopener noreferrer"/);
});

test("does not automatically load external images", () => {
  assert.doesNotMatch(renderMarkdown("![tracking](https://example.com/pixel.png)"), /<img\b/i);
});

test("reparses cumulative streaming chunks without losing text or reference IDs", () => {
  let text = "";
  for (const delta of ["## 결", "과\n\n**확", "인** [ref_", "id:2]"]) {
    text += delta;
    assert.equal(typeof renderMarkdown(text), "string");
  }
  assert.match(renderMarkdown(text), /<h2>결과<\/h2>/);
  assert.match(renderMarkdown(text), /<strong>확인<\/strong>/);
  assert.match(renderMarkdown(text), /\[ref_id:2\]/);
});

test("empty answers render without placeholder content", () => {
  assert.equal(renderMarkdown(""), "");
});

test("table alignment uses classes compatible with strict CSP", () => {
  const html = renderMarkdown("| L | C | R |\n| :--- | :---: | ---: |\n| a | b | c |");
  assert.match(html, /class="align-left"/);
  assert.match(html, /class="align-center"/);
  assert.match(html, /class="align-right"/);
  assert.doesNotMatch(html, /style=/);
});
