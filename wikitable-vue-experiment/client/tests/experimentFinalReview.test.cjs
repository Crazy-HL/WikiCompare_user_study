const assert = require("assert");
const fs = require("fs");
const path = require("path");

const apiSource = fs.readFileSync(path.join(__dirname, "../src/experiment/experimentApi.js"), "utf8");
assert(!apiSource.includes("http://localhost:8888"), "experiment API must not hardcode localhost");
assert(apiSource.includes("VUE_APP_EXPERIMENT_API_BASE"), "experiment API should support an env-configured API base");
assert(apiSource.includes("getStaticTable"), "participant API should expose static-table fetch");
assert(apiSource.includes("adminStaticTable"), "admin API should expose static-table management");

const shellSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/ExperimentShell.vue"), "utf8");
assert(shellSource.includes("getStaticTable"), "ExperimentShell should fetch frozen static table data");
assert(shellSource.includes(":frozen-rows=\"staticTableRows\""), "ExperimentShell should pass frozen rows to ChatGptCondition");
assert(shellSource.includes("stage.condition === 'chatgpt'") && /Static table/.test(shellSource), "ChatGPT stages should be blocked when the static table is unavailable");
assert(shellSource.includes("payload.frozen"), "ExperimentShell should guard against unfrozen public question payloads");

const chatSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/ChatGptCondition.vue"), "utf8");
assert(chatSource.includes("frozenRows"), "ChatGptCondition should render only frozen rows supplied by participant API");
assert(!chatSource.includes("rankedRows"), "ChatGptCondition must not derive rows from live WikiCompare state");

const adminQuestionsSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/AdminQuestions.vue"), "utf8");
assert(adminQuestionsSource.includes("adminStaticTable"), "AdminQuestions should manage static tables");
assert(/questionPayload\?\.frozen[\s\S]*raw-questions-json/.test(adminQuestionsSource) || adminQuestionsSource.includes("questionsFrozen"), "AdminQuestions should disable question save while frozen");
assert(/staticTablePayload\?\.frozen/.test(adminQuestionsSource), "AdminQuestions should disable static-table save while frozen");

const submissionsSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/AdminSubmissions.vue"), "utf8");
assert(submissionsSource.includes("<details"), "AdminSubmissions should include expandable details");
for (const expected of ["questionId", "primarySource", "leftEvidence", "rightEvidence", "durationMs", "stageDurationMs"]) {
	assert(submissionsSource.includes(expected), `AdminSubmissions should display ${expected}`);
}
assert(!submissionsSource.includes("http://localhost:8888"), "AdminSubmissions export links must not hardcode localhost");

console.log("experiment final review source tests passed");
