import test from "node:test";
import assert from "node:assert/strict";
import {questionChoices, questionFromSelection, matchingQuestion} from "../static/question-picker.js";

const questions = [
  {kb: "process", question: "공정 질문 A"},
  {kb: "process", question: "공정 질문 B"},
  {kb: "quality", question: "품질 질문"}
];

test("lists every workshop question, including multiple questions for the same KB", () => {
  const choices = questionChoices(questions);
  assert.equal(3, choices.length);
  assert.deepEqual(choices.map(choice => choice.value), ["0", "1", "2"]);
  assert.equal(choices[0].group, choices[1].group);
  assert.notEqual(choices[0].group, choices[2].group);
  assert.equal(choices[1].question, "공정 질문 B");
});

test("selection returns the exact question and associated KB without rewriting it", () => {
  assert.deepEqual(questionFromSelection(questions, "1"), questions[1]);
  assert.deepEqual(questionFromSelection(questions, "2"), questions[2]);
  assert.equal(questionFromSelection(questions, ""), null);
});

test("manual edits are not mislabelled as an unchanged sample", () => {
  assert.equal(matchingQuestion(questions, "process", "공정 질문 B"), "1");
  assert.equal(matchingQuestion(questions, "process", "공정 질문 B를 수정"), "");
  assert.equal(matchingQuestion(questions, "quality", "공정 질문 B"), "");
});

test("invalid selection is rejected rather than selecting the first question", () => {
  for (const value of ["-1", "3", "1suffix", "__proto__", "01"]) {
    assert.throws(() => questionFromSelection(questions, value), /선택/);
  }
});

test("dialog headings stay short while the complete question is preserved separately", () => {
  const question = "긴 질문 ".repeat(100);
  const choice = questionChoices([{kb: "process", question}])[0];
  assert.equal(choice.label, "질문 1");
  assert.equal(choice.question, question);
});
