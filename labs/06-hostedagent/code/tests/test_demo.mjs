import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {loadDemo, recordingFor, replay, validateDemo} from "../static/demo.js";

const readJSON = name => readFile(new URL(`../static/demo/${name}.json`, import.meta.url), "utf8").then(JSON.parse);

test("all-KS validation rejects a completed response missing a final source citation", () => {
  const catalogs = {};
  const cases = [];
  for (const kb of ["process", "quality"]) {
    const sources = Array.from({length: kb === "process" ? 3 : 4}, (_, i) => ({
      name: `${kb}-${i}`, ok: true, references: 1, cited: 1
    }));
    catalogs[kb] = {name: kb, sources};
    for (let i = 0; i < 2; i++) cases.push({
      kb, question: `${kb}-${i}`, reasoning_effort: "medium", recorded_at: "2026-10-08T00:00:00Z",
      events: [
        {name: "trace", data: {references: sources.map((source, id) => ({id: String(id), source: source.name}))}},
        {name: "delta", data: {text: sources.map((_, id) => `[ref_id:${id}]`).join(" ")}},
        {name: "done", data: {reasoning_effort: "medium", retrieval_seconds: 1,
          trace_metrics: {}, evidence: {passed: true, sources}}}
      ]
    });
  }
  const data = {schema_version: 1, catalogs, cases};
  assert.equal(validateDemo(data), data);
  data.cases[0].events[1].data.text = "[ref_id:0]";
  assert.throws(() => validateDemo(data), /모든 KS/);
});

test("the public recording contains exactly two real, complete Medium runs per KB", async () => {
  const data = validateDemo(await readJSON("recordings"));
  for (const kb of ["process", "quality"]) {
    assert.equal(data.cases.filter(item => item.kb === kb).length, 2);
    assert.equal(data.catalogs[kb].sources.length, kb === "process" ? 3 : 4);
  }
  for (const item of data.cases) {
    assert.equal(item.reasoning_effort, "medium");
    assert.ok(Number.isFinite(Date.parse(item.recorded_at)));
    assert.equal(item.events.at(-1).name, "done");
    const evidence = item.events.at(-1).data.evidence;
    assert.equal(evidence.passed, true, `${item.kb}: all KS must return AND be cited`);
    assert.equal(evidence.sources.length, item.kb === "process" ? 3 : 4);
    assert.ok(evidence.sources.every(source => source.ok && source.references > 0 && source.cited > 0));
    const trace = item.events.find(event => event.name === "trace").data;
    const answer = item.events.filter(event => event.name === "delta").map(event => event.data.text).join("");
    const cited = new Set([...answer.matchAll(/\[ref_id:([^\]]+)\]/g)].map(match => match[1]));
    for (const source of evidence.sources) {
      assert.ok(trace.references.some(ref => ref.source === source.name && cited.has(String(ref.id))),
        `${item.kb}: final displayed answer must cite ${source.name}`);
    }
    assert.ok(item.events.some(event => event.name === "trace" && event.data.references.length));
    assert.ok(item.events.some(event => event.name === "delta" && event.data.text));
    assert.ok(!item.events.some(event => event.name === "error"));
    assert.equal(recordingFor(data, item), item);
  }
});

test("unknown questions, KBs and unrecorded reasoning modes never return a canned answer", async () => {
  const data = await readJSON("recordings");
  const item = data.cases[0];
  for (const change of [{question: "미등록 질문"}, {kb: "unknown"}, {reasoning_effort: "low"}]) {
    assert.throws(() => recordingFor(data, {...item, ...change}), /기록된 질문/);
  }
});

test("broken or incomplete recordings fail explicitly", async () => {
  const data = await readJSON("recordings");
  assert.throws(() => validateDemo({}), /데모 기록/);
  assert.throws(() => validateDemo({...data, cases: data.cases.slice(1)}), /데모 기록/);
  const broken = structuredClone(data);
  broken.cases[0].events.pop();
  assert.throws(() => validateDemo(broken), /데모 기록/);
  const partial = structuredClone(data);
  partial.cases[0].events.at(-1).data.evidence.passed = false;
  assert.throws(() => validateDemo(partial), /모든 KS/);
});

test("replay preserves recorded evidence and trace and can be cancelled then restarted", async () => {
  const {cases: [record]} = await readJSON("recordings");
  const controller = new AbortController();
  const iterator = replay(record, controller.signal);
  assert.deepEqual((await iterator.next()).value, record.events[0]);
  controller.abort();
  await assert.rejects(iterator.next(), {name: "AbortError"});
  const alreadyAborted = new AbortController();
  alreadyAborted.abort();
  await assert.rejects(replay(record, alreadyAborted.signal).next(), {name: "AbortError"});
  const events = [];
  for await (const event of replay(record, new AbortController().signal)) events.push(event);
  assert.deepEqual(events, record.events);
  assert.notEqual(events[0], record.events[0]);
});

test("demo data loads from a public static file; HTTP failure is not replaced with success", async () => {
  const data = await readJSON("recordings");
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async path => {
      assert.equal(path, "/static/demo/recordings.json");
      return new Response(JSON.stringify(data));
    };
    assert.deepEqual(await loadDemo(), data);
    globalThis.fetch = async () => new Response("Unavailable", {status: 503});
    await assert.rejects(loadDemo(), /503/);
  } finally {
    globalThis.fetch = original;
  }
});

test("all ten observed workshop emails have distinct full bodies, not previews", async () => {
  const data = await readJSON("mail");
  assert.equal(data.messages.length, 10);
  assert.equal(new Set(data.messages.map(mail => mail.id)).size, 10);
  assert.equal(new Set(data.messages.map(mail => mail.subject)).size, 10);
  assert.equal(new Set(data.messages.map(mail => mail.body)).size, 10);
  for (const mail of data.messages) {
    assert.match(mail.body, /실습 묶음: IQ-DEMO-20260922/);
    assert.match(mail.body, /워크숍용 가상 업무 자료/);
    assert.ok(mail.body.length > 300);
    assert.ok(!mail.body.endsWith("…"));
  }
});

test("public fixtures contain no session, authorization, email addresses or signed URLs", async () => {
  for (const name of ["recordings", "mail"]) {
    const text = JSON.stringify(await readJSON(name));
    assert.doesNotMatch(text, /Bearer\s+[a-z0-9._-]+|eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]+/i);
    assert.doesNotMatch(text, /[?&](sig|token|access_token)=/i);
    assert.doesNotMatch(text, /"(?:(?:access|refresh|id)_token|csrf|cookie|client_secret)"\s*:/i);
    assert.doesNotMatch(text, /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i);
  }
});
