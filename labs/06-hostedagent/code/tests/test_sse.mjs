import test from "node:test";
import assert from "node:assert/strict";
import {readEvents} from "../static/sse.js";

test("SSE preserves Korean text across arbitrary UTF-8 chunks and ignores heartbeats", async () => {
  const bytes = new TextEncoder().encode(': keep-alive\n\nevent: delta\ndata: {"text":"한국어\\n답변"}\n\nevent: done\ndata: {"ok":true}\n\n');
  const stream = new ReadableStream({
    start(controller) {
      for (let i = 0; i < bytes.length; i += 2) controller.enqueue(bytes.slice(i, i + 2));
      controller.close();
    }
  });
  const events = [];
  for await (const event of readEvents(stream)) events.push(event);
  assert.deepEqual(events, [
    {name: "delta", data: {text: "한국어\n답변"}}, {name: "done", data: {ok: true}}
  ]);
});

test("SSE rejects truncated frames", async () => {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode('event: delta\ndata: {"text":'));
      controller.close();
    }
  });

  await assert.rejects(async () => {
    for await (const event of readEvents(stream)) assert.fail(JSON.stringify(event));
  }, /도중 종료/);
});

test("SSE releases a completed reader without cancelling the successful request", async () => {
  let cancelled = false;
  let released = false;
  const body = {getReader: () => ({
    read: async () => ({done: true}),
    cancel: async () => {cancelled = true;},
    releaseLock: () => {released = true;}
  })};
  for await (const event of readEvents(body)) assert.fail(JSON.stringify(event));
  assert.equal(cancelled, false);
  assert.equal(released, true);
});
