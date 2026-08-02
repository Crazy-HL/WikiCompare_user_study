const assert = require("assert");
const {
	normalizeParticipantCode,
	assignmentForCode,
	validateAssignmentStages,
} = require("../src/experiment/assignment.js");

assert.strictEqual(normalizeParticipantCode("p1"), "P01");
assert.strictEqual(normalizeParticipantCode(" P09 "), "P09");
assert.strictEqual(normalizeParticipantCode("12"), "P12");

const cases = [
	["P01", "S1", "wikicompare", "M1", "chatgpt", "M2"],
	["P02", "S2", "chatgpt", "M2", "wikicompare", "M1"],
	["P03", "S3", "chatgpt", "M1", "wikicompare", "M2"],
	["P04", "S4", "wikicompare", "M2", "chatgpt", "M1"],
	["P16", "S4", "wikicompare", "M2", "chatgpt", "M1"],
];

for (const [code, group, firstCondition, firstMaterial, secondCondition, secondMaterial] of cases) {
	const assignment = assignmentForCode(code);
	assert.strictEqual(assignment.group, group);
	assert.deepStrictEqual(assignment.stages, [
		{ stageIndex: 1, condition: firstCondition, materialId: firstMaterial },
		{ stageIndex: 2, condition: secondCondition, materialId: secondMaterial },
	]);
}

for (const badCode of ["", "P0", "PX", "A01", "P-1"]) {
	assert.throws(() => assignmentForCode(badCode), /Participant code/);
}

assert.strictEqual(validateAssignmentStages(assignmentForCode("P01")), "");
assert.match(
	validateAssignmentStages({ participantCode: "P01", group: "S1", stages: [
		{ stageIndex: 1, condition: "wikicompare", materialId: "M1" },
	] }),
	/实验分配异常/
);
assert.match(
	validateAssignmentStages({ participantCode: "P01", assignmentGroup: "S1", stages: [
		{ stageIndex: 1, condition: "wikicompare", materialId: "M1" },
		{ stageIndex: 2, condition: "wikicompare", materialId: "M2" },
	] }),
	/实验分配异常/
);
assert.match(
	validateAssignmentStages({ participantCode: "P01", group: "S1", stages: [
		{ stageIndex: 1, condition: "chatgpt", materialId: "M2" },
		{ stageIndex: 2, condition: "wikicompare", materialId: "M1" },
	] }),
	/实验分配异常/
);

console.log("experiment assignment tests passed");
