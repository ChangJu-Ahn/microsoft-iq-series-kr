import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const fixture = name => readFile(new URL(`../static/demo/${name}`, import.meta.url));

test("both KB setting snapshots agree with their observed catalogs", async () => {
  const settings = JSON.parse(await fixture("iq-settings.json"));
  const {catalogs} = JSON.parse(await fixture("recordings.json"));
  for (const kb of ["process", "quality"]) {
    const item = settings[kb];
    assert.equal(item.name, catalogs[kb].name);
    assert.equal(item.reasoning_effort.toLowerCase(), catalogs[kb].default_reasoning_effort);
    assert.equal(item.output_mode, "Answer synthesis");
    assert.deepEqual(new Set(item.sources), new Set(catalogs[kb].sources.map(source => source.name)));
    assert.ok(item.retrieval_instructions.length > 100);
    assert.ok(item.answer_instructions.length > 50);
    assert.equal(item.model, "gpt-5.2 (foundry-changju-kr-v2)");
  }
  assert.doesNotMatch(JSON.stringify(settings), /Bearer |client_secret|@[a-z0-9.-]+\.[a-z]{2,}/i);
});

test("two distinct expanded Fabric captures and both KB screenshots are packaged PNGs", async () => {
  const images = [];
  for (const name of ["foundry-process.png", "foundry-quality.png", "fabric-legacy.png", "fabric-new.png"]) {
    const bytes = await fixture(name);
    assert.equal(bytes.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
    assert.ok(bytes.readUInt32BE(16) >= 700, `${name}: capture width`);
    assert.ok(bytes.readUInt32BE(20) >= 700, `${name}: capture height`);
    images.push(bytes);
  }
  assert.notDeepEqual(images[2], images[3], "legacy and new must not reuse one image");
});
