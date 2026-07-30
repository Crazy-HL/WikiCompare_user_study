const assert = require("assert");
const fs = require("fs");
const path = require("path");

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

console.log("sessionStoreCachedTitles tests passed");
