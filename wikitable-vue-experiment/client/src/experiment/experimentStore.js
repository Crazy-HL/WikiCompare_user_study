const { durationMs } = require("./timing.js");

const toQuestionId = question => question.question_id || question.questionId || "";
const toQuestionText = question => question.question_text || question.questionText || "";
const toIsoTimestamp = timestampMs => (Number.isFinite(timestampMs) ? new Date(timestampMs).toISOString() : undefined);

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
	buildCompletionPayload,
	createAnswerRecord,
};
