const GROUP_STAGES = {
	S1: [
		{ stageIndex: 1, condition: "wikicompare", materialId: "M1" },
		{ stageIndex: 2, condition: "chatgpt", materialId: "M2" },
	],
	S2: [
		{ stageIndex: 1, condition: "chatgpt", materialId: "M2" },
		{ stageIndex: 2, condition: "wikicompare", materialId: "M1" },
	],
	S3: [
		{ stageIndex: 1, condition: "chatgpt", materialId: "M1" },
		{ stageIndex: 2, condition: "wikicompare", materialId: "M2" },
	],
	S4: [
		{ stageIndex: 1, condition: "wikicompare", materialId: "M2" },
		{ stageIndex: 2, condition: "chatgpt", materialId: "M1" },
	],
};

const PARTICIPANT_SAFE_ASSIGNMENT_ERROR = "实验分配异常，请联系研究人员。";

const groupForNumber = number => ["S1", "S2", "S3", "S4"][(number - 1) % 4];

const normalizeParticipantCode = value => {
	const raw = String(value || "").trim().toUpperCase();
	if (!raw) throw new Error("Participant code is required");
	let number;
	if (/^\d+$/.test(raw)) {
		number = Number(raw);
	} else {
		const match = raw.match(/^P(\d+)$/);
		if (!match) throw new Error("Participant code must look like P01");
		number = Number(match[1]);
	}
	if (!Number.isInteger(number) || number < 1) {
		throw new Error("Participant code number must be at least 1");
	}
	return `P${String(number).padStart(2, "0")}`;
};

const assignmentForCode = value => {
	const participantCode = normalizeParticipantCode(value);
	const number = Number(participantCode.slice(1));
	const group = groupForNumber(number);
	return {
		participantCode,
		group,
		stages: GROUP_STAGES[group].map(stage => ({ ...stage })),
	};
};

const stageSignature = stage => `${stage?.stageIndex}:${stage?.condition}:${stage?.materialId}`;

const hasExactlyExpectedSystemsAndMaterials = stages => {
	const conditions = stages.map(stage => stage?.condition).sort();
	const materialIds = stages.map(stage => stage?.materialId).sort();
	return (
		conditions.length === 2 &&
		conditions[0] === "chatgpt" &&
		conditions[1] === "wikicompare" &&
		materialIds.length === 2 &&
		materialIds[0] === "M1" &&
		materialIds[1] === "M2"
	);
};

const validateAssignmentStages = assignment => {
	const stages = Array.isArray(assignment?.stages) ? assignment.stages : [];
	if (stages.length !== 2) return PARTICIPANT_SAFE_ASSIGNMENT_ERROR;
	if (stageSignature(stages[0]).split(":")[0] !== "1" || stageSignature(stages[1]).split(":")[0] !== "2") {
		return PARTICIPANT_SAFE_ASSIGNMENT_ERROR;
	}
	if (!hasExactlyExpectedSystemsAndMaterials(stages)) return PARTICIPANT_SAFE_ASSIGNMENT_ERROR;

	const group = assignment?.assignmentGroup || assignment?.group || "";
	const expectedStages = GROUP_STAGES[group];
	if (expectedStages) {
		const expectedSignature = expectedStages.map(stageSignature).join("|");
		const actualSignature = stages.map(stageSignature).join("|");
		if (actualSignature !== expectedSignature) return PARTICIPANT_SAFE_ASSIGNMENT_ERROR;
	}
	return "";
};

module.exports = {
	GROUP_STAGES,
	PARTICIPANT_SAFE_ASSIGNMENT_ERROR,
	assignmentForCode,
	normalizeParticipantCode,
	validateAssignmentStages,
};
