const assert = require("assert");
const fs = require("fs");
const path = require("path");

const {
	conversationHistoryFromMessages,
} = require("../src/js/conversationHistory.js");

assert.deepStrictEqual(
	conversationHistoryFromMessages([
		{ role: "assistant", content: "Comparison session loaded." },
		{
			role: "user",
			content: "Which country has higher remittances?",
			conversationContent: "Which country has higher remittances?",
		},
		{
			role: "assistant",
			content: "<div>India has the higher value.</div>",
			conversationContent: "India has the higher value at 3.5% of GDP.",
		},
		{
			role: "assistant",
			content: "Request failed",
			conversationContent: "Request failed",
			error: true,
		},
	]),
	[
		{ role: "user", content: "Which country has higher remittances?" },
		{ role: "assistant", content: "India has the higher value at 3.5% of GDP." },
	]
);

const longHistory = Array.from({ length: 20 }, (_, index) => ({
	role: index % 2 === 0 ? "user" : "assistant",
	conversationContent: `turn-${index}`,
}));
const boundedHistory = conversationHistoryFromMessages(longHistory);
assert.strictEqual(boundedHistory.length, 12);
assert.strictEqual(boundedHistory[0].content, "turn-8");
assert.strictEqual(boundedHistory[11].content, "turn-19");

const div2Source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "Div2.vue"),
	"utf8"
);

assert(
	div2Source.includes("conversationHistoryFromMessages") &&
		div2Source.includes("conversationHistory: conversationHistory") &&
		div2Source.indexOf("const conversationHistory = conversationHistoryFromMessages") <
			div2Source.indexOf('role: "user"'),
	"Div2 should capture prior visible turns before pushing and sending the current question"
);

console.log("conversationHistory tests passed");
