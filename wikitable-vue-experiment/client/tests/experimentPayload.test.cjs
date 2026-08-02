const assert = require("assert");
const { Q6_TEXT } = require("../src/experiment/q6.js");
const { createAnswerRecord, buildCompletionPayload } = require("../src/experiment/experimentStore.js");

assert(/在阅读两篇文章/.test(Q6_TEXT));

const answer = createAnswerRecord(
	{ question_id: "Q1", question_text: "Question text" },
	{ startedAtMs: 1000, submittedAtMs: 4000, durationMs: 3000 },
	{ answer: "Answer", primarySource: "A", leftEvidence: "L-P001", rightEvidence: "R-P001" }
);
assert.deepStrictEqual(answer, {
	questionId: "Q1",
	questionText: "Question text",
	answer: "Answer",
	primarySource: "A",
	leftEvidence: "L-P001",
	rightEvidence: "R-P001",
	answerStartedAtMs: 1000,
	submittedAtMs: 4000,
	durationMs: 3000,
});

const payload = buildCompletionPayload({
	experimentId: "exp-local",
	participantCode: "P01",
	assignmentGroup: "S1",
	startedAtMs: 10,
	completedAtMs: 1010,
	stages: [{ stageIndex: 1, condition: "wikicompare", materialId: "M1", answers: [answer] }],
});
assert.strictEqual(payload.startedAtMs, 10);
assert.strictEqual(payload.completedAtMs, 1010);
assert.strictEqual(payload.startedAt, "1970-01-01T00:00:00.010Z");
assert.strictEqual(payload.completedAt, "1970-01-01T00:00:01.010Z");
assert.strictEqual(payload.totalDurationMs, 1000);
assert.strictEqual(payload.stages[0].answers[0].primarySource, "A");

const falsyAnswer = createAnswerRecord(
	{ questionId: "Q2", questionText: "Falsy values" },
	{ startedAtMs: 2000, submittedAtMs: 2500, durationMs: 500 },
	{ answer: 0, primarySource: false, leftEvidence: null, rightEvidence: undefined }
);
assert.strictEqual(falsyAnswer.answer, "0");
assert.strictEqual(falsyAnswer.primarySource, "false");
assert.strictEqual(falsyAnswer.leftEvidence, "");
assert.strictEqual(falsyAnswer.rightEvidence, "");

console.log("experiment payload tests passed");
