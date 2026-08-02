const { durationMs } = require("./timing.js");

const toQuestionId = question => question.question_id || question.questionId || "";
const toQuestionText = question => question.question_text || question.questionText || "";
const toIsoTimestamp = timestampMs => (Number.isFinite(timestampMs) ? new Date(timestampMs).toISOString() : undefined);

const REQUIRED_STAGE_QUESTION_COUNT = 5;
const REQUIRED_STAGE_ANSWER_COUNT = REQUIRED_STAGE_QUESTION_COUNT + 1;

const normalizeAnswerQuestionId = answer => String(answer?.questionId || answer?.question_id || "").trim().toUpperCase();

const validateStageAnswerRecords = (answers, expectedQuestionCount = REQUIRED_STAGE_QUESTION_COUNT) => {
	if (!Array.isArray(answers) || answers.length < expectedQuestionCount) {
		return `本阶段需要提交 ${expectedQuestionCount + 1} 条答案。`;
	}
	for (let index = 0; index < expectedQuestionCount; index += 1) {
		const expectedId = `Q${index + 1}`;
		if (normalizeAnswerQuestionId(answers[index]) !== expectedId) {
			return `本阶段答案不完整：缺少 ${expectedId}。`;
		}
	}
	if (normalizeAnswerQuestionId(answers[expectedQuestionCount]) !== "Q6") {
		return "本阶段答案不完整：缺少 Q6。";
	}
	if (answers.length !== expectedQuestionCount + 1) {
		return `本阶段需要提交 ${expectedQuestionCount + 1} 条答案。`;
	}
	return "";
};

const createAnswerRecord = (question, timing, values = {}) => ({
	questionId: toQuestionId(question),
	questionText: toQuestionText(question),
	answer: String(values.answer ?? ""),
	primarySource: String(values.primarySource ?? ""),
	leftEvidence: String(values.leftEvidence ?? ""),
	rightEvidence: String(values.rightEvidence ?? ""),
	answerStartedAtMs: timing.startedAtMs,
	submittedAtMs: timing.submittedAtMs,
	durationMs: timing.durationMs,
});

const buildCompletionPayload = state => ({
	experimentId: state.experimentId,
	participantCode: state.participantCode,
	assignmentGroup: state.assignmentGroup,
	startedAt: toIsoTimestamp(state.startedAtMs),
	completedAt: toIsoTimestamp(state.completedAtMs),
	startedAtMs: state.startedAtMs,
	completedAtMs: state.completedAtMs,
	totalDurationMs: durationMs(state.startedAtMs, state.completedAtMs),
	stages: (state.stages || []).map(stage => ({
		stageIndex: stage.stageIndex,
		condition: stage.condition,
		materialId: stage.materialId,
		questionVersion: stage.questionVersion || 0,
		stageStartedAtMs: stage.stageStartedAtMs,
		stageSubmittedAtMs: stage.stageSubmittedAtMs,
		stageDurationMs: durationMs(stage.stageStartedAtMs, stage.stageSubmittedAtMs),
		answers: stage.answers || [],
	})),
	browser: {
		userAgent: typeof navigator === "undefined" ? "node" : navigator.userAgent,
	},
});

module.exports = {
	REQUIRED_STAGE_ANSWER_COUNT,
	REQUIRED_STAGE_QUESTION_COUNT,
	buildCompletionPayload,
	createAnswerRecord,
	validateStageAnswerRecords,
};
