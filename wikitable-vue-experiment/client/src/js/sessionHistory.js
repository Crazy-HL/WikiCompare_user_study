const HISTORY_STORAGE_KEY = "wikicompare_compare_history";
const ACTIVE_SESSION_STORAGE_KEY = "wikicompare_active_compare_session";
const DEFAULT_HISTORY_LIMIT = 8;

function normalizeUrl(value) {
	return String(value || "").trim().replace(/\/+$/, "");
}

function sessionPairKey(session) {
	const leftUrl = normalizeUrl(session?.articles?.left?.url);
	const rightUrl = normalizeUrl(session?.articles?.right?.url);
	return pairKey(leftUrl, rightUrl);
}

function pairKey(leftUrl, rightUrl) {
	return `${normalizeUrl(leftUrl)}||${normalizeUrl(rightUrl)}`;
}

function historyRecordFromSession(session, timestamp = Date.now()) {
	const left = session?.articles?.left || {};
	const right = session?.articles?.right || {};
	return {
		key: sessionPairKey(session),
		sessionId: session?.sessionId || "",
		leftTitle: left.title || "Left article",
		rightTitle: right.title || "Right article",
		leftUrl: normalizeUrl(left.url),
		rightUrl: normalizeUrl(right.url),
		updatedAt: timestamp,
		session,
	};
}

function addSessionToHistory(history, session, limit = DEFAULT_HISTORY_LIMIT, timestamp = Date.now()) {
	if (!session || !session.sessionId || !session?.articles?.left || !session?.articles?.right) {
		return Array.isArray(history) ? history : [];
	}
	const record = historyRecordFromSession(session, timestamp);
	const existing = Array.isArray(history) ? history : [];
	return [
		record,
		...existing.filter(item => item && item.key !== record.key),
	].slice(0, limit);
}

function findHistoryByUrls(history, leftUrl, rightUrl) {
	const key = pairKey(leftUrl, rightUrl);
	return (Array.isArray(history) ? history : []).find(item => item && item.key === key) || null;
}

function findHistoryByKey(history, key) {
	return (Array.isArray(history) ? history : []).find(item => item && item.key === key) || null;
}

function removeHistoryByKey(history, key) {
	return (Array.isArray(history) ? history : []).filter(
		item => item && item.key !== key
	);
}

function loadHistory(storage = browserStorage()) {
	if (!storage) return [];
	let records = [];
	try {
		const parsed = JSON.parse(storage.getItem(HISTORY_STORAGE_KEY) || "[]");
		records = Array.isArray(parsed)
			? parsed.filter(isValidRecord).slice(0, DEFAULT_HISTORY_LIMIT)
			: [];
	} catch (_error) {
		records = [];
	}
	const activeSession = loadActiveSession(storage);
	if (!activeSession) return records;
	const activeKey = sessionPairKey(activeSession);
	const activeIndex = records.findIndex(record => record?.key === activeKey);
	if (activeIndex >= 0) {
		records[activeIndex] = {
			...records[activeIndex],
			session: activeSession,
		};
		return records;
	}
	return [historyRecordFromSession(activeSession), ...records].slice(0, DEFAULT_HISTORY_LIMIT);
}

function saveHistory(storage = browserStorage(), history = []) {
	if (!storage) return;
	const sourceHistory = Array.isArray(history) ? history : [];
	const activeSession = sourceHistory.find(record => record?.session)?.session || null;
	if (activeSession) {
		try {
			storage.setItem(ACTIVE_SESSION_STORAGE_KEY, JSON.stringify(activeSession));
		} catch (_error) {
			// The lightweight history below should still be saved if the full session is too large.
		}
	}
	const compactHistory = sourceHistory
		.slice(0, DEFAULT_HISTORY_LIMIT)
		.map(compactRecord)
		.filter(isValidRecord);
	try {
		storage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(compactHistory));
	} catch (_error) {
		// Ignore storage quota failures so a loaded comparison session is not disrupted.
	}
}

function loadActiveSession(storage) {
	try {
		const session = JSON.parse(storage.getItem(ACTIVE_SESSION_STORAGE_KEY) || "null");
		if (!session || !session.sessionId || !session?.articles?.left || !session?.articles?.right) {
			return null;
		}
		return session;
	} catch (_error) {
		return null;
	}
}

function isValidRecord(record) {
	return Boolean(
		record &&
		record.key &&
		record.sessionId &&
		record.leftUrl &&
		record.rightUrl
	);
}

function compactRecord(record) {
	return {
		key: record.key,
		sessionId: record.sessionId,
		leftTitle: record.leftTitle,
		rightTitle: record.rightTitle,
		leftUrl: record.leftUrl,
		rightUrl: record.rightUrl,
		updatedAt: record.updatedAt,
	};
}

function browserStorage() {
	if (typeof window === "undefined" || !window.localStorage) return null;
	return window.localStorage;
}

module.exports = {
	ACTIVE_SESSION_STORAGE_KEY,
	HISTORY_STORAGE_KEY,
	DEFAULT_HISTORY_LIMIT,
	addSessionToHistory,
	findHistoryByKey,
	findHistoryByUrls,
	historyRecordFromSession,
	loadHistory,
	normalizeUrl,
	pairKey,
	removeHistoryByKey,
	saveHistory,
	sessionPairKey,
};
