import test from "node:test";
import assert from "node:assert/strict";
import {summarizeQuery, summarizeRepeat, executionPasses, modelTokenCount} from "../static/trace.js";

test("normalizes Search, Blob, Fabric and Work IQ searches into the same fields", () => {
  for (const field of ["searchIndexArguments", "azureBlobArguments", "fabricDataAgentArguments", "workIQArguments"]) {
    const row = summarizeQuery({id: 2, source: "source", count: 0,
      arguments: {[field]: {search: "실제 하위 검색어", filter: "lot_id eq 'LOT0012'"}}});
    assert.equal(row.query, "실제 하위 검색어");
    assert.equal(row.filter, "lot_id eq 'LOT0012'");
    assert.equal(row.count, 0);
    assert.equal(row.tool, "미제공");
  }
});

test("normalizes MCP tool arguments, including encoded JSON, without hiding lookup inputs", () => {
  const row = summarizeQuery({id: 3, count: 2, arguments: {
    mcpServerArguments: {toolName: "get_lot", toolArguments: '{"lot_id":"LOT0012"}'}
  }});
  assert.equal(row.tool, "get_lot");
  assert.match(row.query, /get_lot/);
  assert.match(row.query, /lot_id=LOT0012/);
  const web = summarizeQuery({arguments: {mcpServerArguments: {
    toolName: "web", toolArguments: {query: "public process issue", maxResults: 3}
  }}});
  assert.equal(web.query, "public process issue");
  assert.equal(web.tool, "web");
});

test("unknown input and malformed tool arguments remain explicitly available via raw details", () => {
  const unknown = summarizeQuery({arguments: {futureArguments: {unknown: true}}});
  assert.equal(unknown.query, "검색문 미제공 — 상세 JSON 확인");
  const malformed = summarizeQuery({arguments: {mcpServerArguments: {
    toolName: "tool", toolArguments: '{"broken"'
  }}});
  assert.match(malformed.query, /입력 해석 불가/);
});

test("repeated calls show exact prior and follow-up queries rather than guessed retry reasons", () => {
  const queries = [
    {id: 1, count: 0, arguments: {searchIndexArguments: {search: "first"}}},
    {id: 4, count: 2, arguments: {searchIndexArguments: {search: "second"}}}
  ];
  const row = summarizeRepeat({previousId: 1, id: 4, source: "source",
    previousCount: 0, count: 2, argumentsChanged: true}, queries);
  assert.equal(row.previous.query, "first");
  assert.equal(row.current.query, "second");
  assert.equal(row.previous.count, 0);
  assert.equal(row.current.count, 2);
  assert.match(row.reason, /명시되지/);
});

test("groups returned planning and search activities in observed order", () => {
  const rows = [
    {id:0,type:"modelQueryPlanning"},
    {id:1,type:"mcpServer",source:"mes"},
    {id:2,type:"modelQueryPlanning"},
    {id:3,type:"azureBlob",source:"manual"},
    {id:4,type:"modelAnswerSynthesis"},
    {id:5,type:"agenticReasoning"}
  ];
  const passes = executionPasses(rows);
  assert.equal(passes.length, 2);
  assert.equal(passes[0].planning.id, 0);
  assert.deepEqual(passes[0].activities.map(x=>x.id), [1]);
  assert.deepEqual(passes[1].activities.map(x=>x.id), [3,4,5]);
  assert.equal(passes[1].number, 2);
});

test("does not invent a planning pass when the response has no planning activity", () => {
  const passes = executionPasses([{id:1,type:"searchIndex",source:"source"}]);
  assert.equal(passes[0].number, null);
  assert.equal(passes[0].planning, null);
  assert.deepEqual(executionPasses([]), []);
});

test("token summary counts explicit model I/O once and leaves absent values unknown", () => {
  assert.equal(modelTokenCount([
    {type:"modelQueryPlanning",details:{inputTokens:100,outputTokens:20}},
    {type:"modelAnswerSynthesis",details:{inputTokens:200,outputTokens:30}},
    {type:"agenticReasoning",details:{reasoningTokens:500}}
  ]),350);
  assert.equal(modelTokenCount([{type:"searchIndex",details:{}}]),null);
});
