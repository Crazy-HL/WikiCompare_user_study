const assert = require("assert");
const { durationMs, createTimingMark } = require("../src/experiment/timing.js");

assert.strictEqual(durationMs(1000, 4500), 3500);
assert.strictEqual(durationMs(4500, 1000), 0);

let current = 100;
const mark = createTimingMark(() => current);
assert.strictEqual(mark.startedAtMs, 100);
current = 250;
const submitted = mark.submit();
assert.strictEqual(submitted.startedAtMs, 100);
assert.strictEqual(submitted.submittedAtMs, 250);
assert.strictEqual(submitted.durationMs, 150);

console.log("experiment timing tests passed");
