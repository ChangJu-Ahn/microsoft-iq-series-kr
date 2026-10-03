const groupLabels = {
  process: "공정 이해 · 현장 조회",
  quality: "품질 이슈 · 후속 조치"
};

export function questionChoices(questions) {
  return questions.map((item, index) => ({
    value: String(index), group: groupLabels[item.kb] || item.kb,
    label: `질문 ${index + 1}`,
    kb: item.kb, question: item.question
  }));
}

export function questionFromSelection(questions, value) {
  if (value === "") return null;
  const index = Number(value);
  if (!Number.isInteger(index) || String(index) !== value || index < 0 || index >= questions.length) {
    throw new RangeError("질문 선택값이 올바르지 않습니다. 목록을 다시 확인하세요.");
  }
  return questions[index];
}

export function matchingQuestion(questions, kb, text) {
  const index = questions.findIndex(item => item.kb === kb && item.question.trim() === text.trim());
  return index < 0 ? "" : String(index);
}
