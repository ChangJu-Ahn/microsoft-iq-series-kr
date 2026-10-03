import test from "node:test";
import assert from "node:assert/strict";
import {comparisonRows} from "../static/comparison.js";

test("comparison includes only identical KB and trimmed question, newest first", () => {
  const history = [
    {kb: "process", question: "q", reasoning_effort: "low"},
    {kb: "quality", question: "q", reasoning_effort: "medium"},
    {kb: "process", question: "different", reasoning_effort: "medium"},
    {kb: "process", question: "q ", reasoning_effort: "medium"}
  ];
  assert.deepEqual(comparisonRows(history, "process", " q ").map(row => row.reasoning_effort), ["medium", "low"]);
  assert.equal(history[0].reasoning_effort, "low");
});

test("comparison does not infer missing timings as zero or compare different questions", () => {
  assert.deepEqual(comparisonRows([{kb: "process", question: "q"}], "process", "other"), []);
  assert.equal(comparisonRows([{kb: "process", question: "q"}], "process", "q")[0].retrieval_seconds, undefined);
});
