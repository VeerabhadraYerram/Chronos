import { readFileSync } from "node:fs";
import { test } from "node:test";
import assert from "node:assert/strict";
import ts from "typescript";
const source = readFileSync(
  new URL("../src/graph-label-layout.ts", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
  },
}).outputText;
const { placeLabels, intersects } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);
function verify(anchors, cards) {
  const placed = placeLabels(anchors, cards);
  assert.equal(placed.length, anchors.length);
  for (let i = 0; i < placed.length; i++) {
    for (const card of cards) assert.equal(intersects(placed[i], card), false);
    for (const label of placed.slice(i + 1))
      assert.equal(intersects(placed[i], label), false);
  }
  return placed;
}
test("dense coincident labels reserve separate rectangles around cards", () => {
  const labels = Array.from({ length: 100 }, (_, i) => ({
    id: String(i),
    x: 0,
    y: 0,
    width: 184,
    height: 36 + (i % 5) * 20,
  }));
  const cards = [{ x: -300, y: -200, width: 1000, height: 600 }];
  const placed = verify(labels, cards);
  assert.deepEqual(placed, placeLabels([...labels].reverse(), cards));
});
test("dragged cards and resized multi-line labels trigger a valid new allocation", () => {
  const labels = Array.from({ length: 35 }, (_, i) => ({
    id: String(i),
    x: (i % 3) * 50,
    y: (i % 4) * 40,
    width: 184,
    height: 56,
  }));
  for (let step = 0; step < 15; step++) {
    verify(
      labels.map((n, i) => ({ ...n, height: i % 2 ? 120 : 36 })),
      [{ x: step * 35 - 200, y: step * 20 - 100, width: 220, height: 240 }],
    );
  }
});
