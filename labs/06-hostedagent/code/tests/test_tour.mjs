import test from "node:test";
import assert from "node:assert/strict";
import {tourSteps, nextTourStep, tourPlacement} from "../static/tour.js";

test("tour follows the ten requested surfaces in order", () => {
  assert.deepEqual(tourSteps.map(step => step.target), [
    "#demo-mail-link", "#demo-foundry-link", "#demo-fabric-link", "#demo-mes-link",
    "#kb", "#question-entry", "#send", "#sources", ".debug-toggle", '[data-tour="timeline"]'
  ]);
  assert.equal(tourSteps.length, 10);
  for (const step of tourSteps) {
    assert.ok(step.title.length && step.text.length);
  }
  assert.match(tourSteps[3].text, /외부.*목업/);
  assert.match(tourSteps[9].text, /겹친|겹치는/);
  assert.match(tourSteps[9].text, /ID.*순서/);
});

test("result steps require completed replay, never elapsed timers or partial answers", () => {
  for (const state of ["idle", "running"]) {
    for (let index = 6; index < 10; index++) assert.equal(nextTourStep(index, state), 6);
  }
  for (let index = 0; index < 6; index++) assert.equal(nextTourStep(index, "idle"), index + 1);
  for (let index = 6; index < 10; index++) assert.equal(nextTourStep(index, "complete"), index + 1);
  assert.throws(() => nextTourStep(-1, "idle"), /단계/);
  assert.throws(() => nextTourStep(10, "idle"), /단계/);
  assert.throws(() => nextTourStep(6, "failed"), /재생 상태/);
});

test("coachmark stays in viewport and avoids targets when space is available", () => {
  const box = {left: 60, right: 360, top: 100, bottom: 145};
  const panel = {width: 320, height: 260};
  const desktop = tourPlacement(box, panel, {width: 1280, height: 900});
  assert.ok(desktop.left > box.right);
  for (const viewport of [{width: 390, height: 844}, {width: 844, height: 390}]) {
    const position = tourPlacement(box, panel, viewport);
    assert.ok(position.left >= 12 && position.left + panel.width <= viewport.width - 12);
    assert.ok(position.top >= 12 && position.top + panel.height <= viewport.height - 12);
  }
});
