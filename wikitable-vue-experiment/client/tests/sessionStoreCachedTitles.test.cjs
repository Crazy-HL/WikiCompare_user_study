const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "sessionStore.js"),
	"utf8"
);

assert(
	source.includes("applySessionTitles") &&
		source.includes("this.applySession(applySessionTitles(cachedRecord.session, options));"),
	"sessionStore should apply requested article titles when reusing a cached comparison session"
);
assert(
	source.includes("this.applySession(applySessionTitles(session, options));"),
	"sessionStore should also normalize requested article titles on fresh compare-session responses"
);
assert(
	source.includes("const initialHistory = loadHistory();") &&
		source.includes("session: initialHistory[0]?.session || null") &&
		source.includes('activeHistoryKey: initialHistory[0]?.key || ""'),
	"sessionStore should restore the latest complete cached comparison on page refresh without making a backend request"
);
assert(
	source.includes("if (initialHistory[0]?.session)") &&
		source.includes("saveHistory(undefined, initialHistory);"),
	"sessionStore should migrate old full-session history entries into the durable latest-session cache during startup"
);

const loadSessionStoreForCachedErrorTest = () => {
	const cachedSession = {
		articles: {
			left: { url: "https://example.test/left", title: "Left" },
			right: { url: "https://example.test/right", title: "Right" }
		}
	};
	const history = [{ key: "cached-key", leftUrl: "https://example.test/left", rightUrl: "https://example.test/right", session: cachedSession }];
	let backendCallCount = 0;
	const transformedSource = source
		.replace('import { reactive } from "vue";', "const reactive = value => value;")
		.replace('import { postJson } from "@/api";', "const postJson = async () => { backendCallCount += 1; return {}; };")
		.replace(/export const /g, "const ");
	const sandbox = {
		module: { exports: {} },
		URL,
		backendCallCount,
		require: dependency => {
			if (dependency === "@/js/offlineSupport") {
				return { isOfflineNow: () => false, WIKICOMPARE_OFFLINE_MESSAGE: "offline" };
			}
			if (dependency === "@/js/sessionHistory") {
				return {
					addSessionToHistory: (records, session) => records.map(record => ({ ...record, session })),
					findHistoryByKey: (records, key) => records.find(record => record.key === key),
					findHistoryByUrls: (records, leftUrl, rightUrl) => records.find(record => record.leftUrl === leftUrl && record.rightUrl === rightUrl),
					loadHistory: () => history,
					removeHistoryByKey: records => records,
					saveHistory: () => {},
					sessionPairKey: () => "cached-key"
				};
			}
			throw new Error(`Unexpected dependency in test: ${dependency}`);
		}
	};
	vm.runInNewContext(
		`${transformedSource}\nmodule.exports = { sessionStore, getBackendCallCount: () => backendCallCount };`,
		sandbox
	);
	return sandbox.module.exports;
};

(async () => {
	const { sessionStore, getBackendCallCount } = loadSessionStoreForCachedErrorTest();
	sessionStore.error = "previous network failure";
	await sessionStore.loadSession("https://example.test/left", "https://example.test/right", {
		leftTitle: "Experiment Left",
		rightTitle: "Experiment Right"
	});
	assert.strictEqual(sessionStore.error, "", "cached loadSession success should clear stale errors");
	assert.strictEqual(getBackendCallCount(), 0, "cached loadSession should not call the backend");
	assert.strictEqual(sessionStore.session.articles.left.title, "Experiment Left", "cached load should still apply requested material titles");

	sessionStore.error = "previous network failure";
	sessionStore.applySession(sessionStore.session);
	assert.strictEqual(sessionStore.error, "", "applySession should clear stale errors for cached selectHistory paths");
	console.log("sessionStoreCachedTitles tests passed");
})().catch(error => {
	console.error(error);
	process.exitCode = 1;
});
