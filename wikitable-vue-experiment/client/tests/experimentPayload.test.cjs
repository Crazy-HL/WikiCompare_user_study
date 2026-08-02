const assert = require("assert");
const { Q6_TEXT } = require("../src/experiment/q6.js");
const fs = require("fs");
const path = require("path");
const { createAnswerRecord, buildCompletionPayload, validateStageAnswerRecords } = require("../src/experiment/experimentStore.js");

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

const completeAnswerSet = Array.from({ length: 5 }, (_, index) => ({
	questionId: `Q${index + 1}`,
	questionText: `Question ${index + 1}`,
	answer: "answer",
})).concat({ questionId: "Q6", questionText: Q6_TEXT, answer: "notes" });
assert.strictEqual(validateStageAnswerRecords(completeAnswerSet), "");
assert.match(validateStageAnswerRecords([{ questionId: "Q6", questionText: Q6_TEXT }]), /6 条/);
assert.match(validateStageAnswerRecords(completeAnswerSet.slice(0, 5)), /Q6/);

const experimentShellSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "experiment", "ExperimentShell.vue"),
	"utf8"
);
assert(
	experimentShellSource.includes('v-if="isStageReady"') &&
		experimentShellSource.includes("validateStageAnswerRecords"),
	"ExperimentShell should only render AnswerPanel after the loaded stage is ready and should validate submitted answer records"
);
const continueStart = experimentShellSource.indexOf("const continueToNextStage = () => {");
const continueEnd = experimentShellSource.indexOf("};", continueStart);
assert(
	continueStart >= 0 && !experimentShellSource.slice(continueStart, continueEnd).includes("loadCurrentStage()"),
	"ExperimentShell should let the current-stage watcher load stage 2 instead of explicitly loading it twice"
);

const chatGptConditionSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "experiment", "ChatGptCondition.vue"),
	"utf8"
);
assert(!chatGptConditionSource.includes("rankedRows"), "ChatGPT static table should not derive frozen rows from the live session rankedRows");
assert(
	chatGptConditionSource.indexOf("const priorConversationHistory") >= 0 &&
		chatGptConditionSource.indexOf("const priorConversationHistory") < chatGptConditionSource.indexOf('messages.value.push({ role: "user"'),
	"ChatGptCondition should build /api/ask conversation history before pushing the current user message"
);

console.log("experiment payload tests passed");
