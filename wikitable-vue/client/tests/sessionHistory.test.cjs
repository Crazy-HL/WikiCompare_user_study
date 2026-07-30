const assert = require("assert");

const {
	ACTIVE_SESSION_STORAGE_KEY,
	addSessionToHistory,
	findHistoryByUrls,
	HISTORY_STORAGE_KEY,
	loadHistory,
	removeHistoryByKey,
	saveHistory,
} = require("../src/js/sessionHistory.js");

function makeSession(sessionId, leftTitle, rightTitle, extra = {}) {
	return {
		sessionId,
		articles: {
			left: {
				title: leftTitle,
				url: `https://en.wikipedia.org/wiki/${leftTitle}`,
			},
			right: {
				title: rightTitle,
				url: `https://en.wikipedia.org/wiki/${rightTitle}`,
			},
		},
		...extra,
	};
}

let history = [];
history = addSessionToHistory(history, makeSession("s1", "Economy_of_A", "Economy_of_B"), 5, 1000);
history = addSessionToHistory(history, makeSession("s2", "Economy_of_C", "Economy_of_D"), 5, 2000);
assert.strictEqual(history.length, 2);
assert.strictEqual(history[0].sessionId, "s2");

const cached = findHistoryByUrls(
	history,
	" https://en.wikipedia.org/wiki/Economy_of_A ",
	"https://en.wikipedia.org/wiki/Economy_of_B"
);
assert.strictEqual(cached.session.sessionId, "s1");

history = addSessionToHistory(history, makeSession("s3", "Economy_of_A", "Economy_of_B"), 5, 3000);
assert.strictEqual(history.length, 2);
assert.strictEqual(history[0].sessionId, "s3");
assert.strictEqual(findHistoryByUrls(history, "https://en.wikipedia.org/wiki/Economy_of_A", "https://en.wikipedia.org/wiki/Economy_of_B").session.sessionId, "s3");

let limited = [];
for (let index = 0; index < 10; index += 1) {
	limited = addSessionToHistory(
		limited,
		makeSession(`s${index}`, `Economy_of_${index}`, `Economy_of_${index + 1}`),
		3,
		index
	);
}
assert.deepStrictEqual(limited.map(item => item.sessionId), ["s9", "s8", "s7"]);

const removed = removeHistoryByKey(history, history[0].key);
assert.strictEqual(removed.length, 1);
assert.strictEqual(removed[0].sessionId, "s2");
assert.deepStrictEqual(removeHistoryByKey(undefined, "missing"), []);

const storage = {};
const fakeStorage = {
	getItem(key) {
		return storage[key] || null;
	},
	setItem(key, value) {
		storage[key] = value;
	},
};
saveHistory(fakeStorage, history);
const loaded = loadHistory(fakeStorage);
assert.strictEqual(loaded.length, 2);
assert.strictEqual(loaded[0].session.sessionId, "s3");
assert.strictEqual(
	findHistoryByUrls(
		loaded,
		"https://en.wikipedia.org/wiki/Economy_of_A",
		"https://en.wikipedia.org/wiki/Economy_of_B"
	).session.sessionId,
	"s3"
);
assert(!storage[HISTORY_STORAGE_KEY].includes('"session"'));
assert(JSON.parse(storage[ACTIVE_SESSION_STORAGE_KEY]).sessionId === "s3");
storage.wikicompare_compare_history = "{bad json";
assert.strictEqual(loadHistory(fakeStorage)[0].session.sessionId, "s3");
storage[ACTIVE_SESSION_STORAGE_KEY] = "{bad json";
assert.deepStrictEqual(loadHistory(fakeStorage), []);

let quotaHistory = [];
quotaHistory = addSessionToHistory(
	quotaHistory,
	makeSession("large1", "Large_A", "Large_B", { sourceMap: { a: "x".repeat(900) } }),
	5,
	1000
);
quotaHistory = addSessionToHistory(
	quotaHistory,
	makeSession("large2", "Large_C", "Large_D", { sourceMap: { b: "y".repeat(900) } }),
	5,
	2000
);
const quotaStorageData = {};
const quotaStorage = {
	getItem(key) {
		return quotaStorageData[key] || null;
	},
	setItem(key, value) {
		if (key === HISTORY_STORAGE_KEY && value.length > 700) {
			throw new Error("QuotaExceededError");
		}
		quotaStorageData[key] = value;
	},
};
assert.doesNotThrow(() => saveHistory(quotaStorage, quotaHistory));
assert(!quotaStorageData[HISTORY_STORAGE_KEY].includes('"sourceMap"'));
assert.strictEqual(loadHistory(quotaStorage)[0].session.sessionId, "large2");

console.log("sessionHistory tests passed");
