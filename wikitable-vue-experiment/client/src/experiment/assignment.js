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

module.exports = {
	GROUP_STAGES,
	assignmentForCode,
	normalizeParticipantCode,
};
