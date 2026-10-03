import test from "node:test";
import assert from "node:assert/strict";
import {indexReferences, sourceInfo, referenceContent} from "../static/references.js";
import {renderMarkdown} from "../static/markdown.js";

test("real citations display readable sources and link to evidence cards", () => {
  const refs = indexReferences([
    {id: "7", source: "ks-process-mes-v2", title: "로트 상태", sourcePreview: "반환 근거"},
    {id: "2", source: "ks-quality-manuals-v2"},
    {id: "4", source: "ks-process-webiq-v2", citationUrl: "https://example.com/article"}
  ]);
  const html = renderMarkdown("상태 [ref_id:7], 점검 [ref_id:2], 공개 사례 [ref_id:4].", refs);
  assert.match(html, /MES · 7/);
  assert.match(html, /내부 매뉴얼 · 2/);
  assert.match(html, /Web IQ · 4/);
  assert.match(html, /href="#evidence-0"/);
  assert.match(html, /data-ref-id="7"/);
});

test("unresolved or ambiguous reference IDs are visibly unverified, not clickable", () => {
  const refs = indexReferences([{id: "1", source: "a"}, {id: "1", source: "b"}]);
  const html = renderMarkdown("문장 [ref_id:missing] [ref_id:1]", refs);
  assert.match(html, /근거 미확인 · missing/);
  assert.match(html, /citation-missing/);
  assert.doesNotMatch(html, /href="#evidence-/);
});

test("reference markers inside code or existing links are not nested citations", () => {
  const refs = indexReferences([{id: "7", source: "ks-process-mes-v2"}]);
  const html = renderMarkdown("`[ref_id:7]`\n\n```\n[ref_id:7]\n```\n\n[[ref_id:7]](https://example.com)", refs);
  assert.doesNotMatch(html, /class="citation/);
  assert.match(html, /<code>\[ref_id:7\]<\/code>/);
});

test("untrusted reference text is escaped and original URLs require safe HTTP(S)", () => {
  const refs = indexReferences([
    {id: '7"onclick="bad', source: '<img src=x onerror=bad>', title: '<script>bad</script>',
      citationUrl: "javascript:bad"},
    {id: "8", source: "ks-quality-workiq-v2"},
    {id: "9", source: "ks-process-webiq-v2", citationUrl: "https://user:pass@example.com"},
    {id: "10", source: "ks-process-webiq-v2", citationUrl: "https://example.com/source"}
  ]);
  const html = renderMarkdown('[ref_id:7"onclick="bad]', refs);
  assert.doesNotMatch(html, /<(img|script)\b/);
  assert.match(html, /&quot;/);
  assert.equal(refs.get('7"onclick="bad').url, null);
  assert.equal(refs.get("8").url, null);
  assert.equal(refs.get("9").url, null);
  assert.equal(refs.get("10").url, "https://example.com/source");
});

test("source labels preserve the actual connected source, including unknown sources", () => {
  assert.equal(sourceInfo("ks-quality-fabric-v2").label, "Fabric");
  assert.equal(sourceInfo("custom-ks").label, "custom-ks");
  assert.equal(sourceInfo("__proto__").label, "__proto__");
  assert.equal(sourceInfo(null).label, "출처 미연결");
});

test("evidence body uses extracted passage and reports its actual field and limit", () => {
  const body = referenceContent({
    sourceContentStatus: "available", sourcePreview: "장비 점검 본문",
    sourceContentField: "sourceData.snippet", sourceContentFormat: "text",
    sourceContentLength: 1994, sourcePreviewLimit: 12000, previewTruncated: false,
    sourceMetadata: {uid: "unrelated-guid"}
  });
  assert.equal(body.text, "장비 점검 본문");
  assert.equal(body.field, "sourceData.snippet");
  assert.equal(body.truncated, false);
  assert.equal(body.total, 1994);
  assert.doesNotMatch(body.text, /guid/);
});

test("missing and legacy JSON previews are not passed off as actual context", () => {
  assert.equal(referenceContent({sourceContentStatus: "missing"}).text, null);
  assert.match(referenceContent({sourceContentStatus: "unavailable"}).label, /본문 필드가 없습니다/);
  const old = referenceContent({sourcePreview: '{"uid":"guid","blob_url":"...'});
  assert.equal(old.text, null);
  assert.match(old.label, /이전 응답/);
});
