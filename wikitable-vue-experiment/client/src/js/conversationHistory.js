const DEFAULT_HISTORY_LIMIT = 12;
const DEFAULT_CONTENT_LIMIT = 4000;
const ALLOWED_ROLES = new Set(["user", "assistant"]);

function conversationHistoryFromMessages(
	messages,
	historyLimit = DEFAULT_HISTORY_LIMIT,
	contentLimit = DEFAULT_CONTENT_LIMIT
) {
	const normalizedHistoryLimit = positiveInteger(historyLimit, DEFAULT_HISTORY_LIMIT);
	const normalizedContentLimit = positiveInteger(contentLimit, DEFAULT_CONTENT_LIMIT);

	return (Array.isArray(messages) ? messages : [])
		.filter(message => message && !message.error && ALLOWED_ROLES.has(message.role))
		.map(message => ({
			role: message.role,
			content: String(message.conversationContent || "")
				.trim()
				.slice(0, normalizedContentLimit),
		}))
		.filter(message => message.content)
		.slice(-normalizedHistoryLimit);
}

function positiveInteger(value, fallback) {
	const numericValue = Number(value);
	return Number.isInteger(numericValue) && numericValue > 0
		? numericValue
		: fallback;
}

module.exports = {
	DEFAULT_CONTENT_LIMIT,
	DEFAULT_HISTORY_LIMIT,
	conversationHistoryFromMessages,
};
