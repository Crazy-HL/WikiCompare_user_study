const assert = require("assert");

const {
	buildCreditRatingPairs,
	parseCreditRatingText,
} = require("../src/js/creditRatingDisplay.js");

const leftRaw = "Standard & Poor's: AA- (Domestic) AA- (Foreign) AA (T&C Assessment) Outlook: Stable Moody's: Aa2 Outlook: Stable Fitch: AA- Outlook: Stable";
const rightRaw = "Standard & Poor's: A+ (Domestic) A+ (Foreign) AA+ (T&C Assessment) Outlook: Stable Moody's: A1 Outlook: Stable Fitch: A Outlook: Stable";

assert.deepStrictEqual(parseCreditRatingText(leftRaw), [
	{
		agency: "S&P",
		fullAgency: "Standard & Poor's",
		items: [
			{ label: "Domestic", value: "AA-" },
			{ label: "Foreign", value: "AA-" },
			{ label: "T&C", value: "AA" },
			{ label: "Outlook", value: "Stable" },
		],
	},
	{
		agency: "Moody's",
		fullAgency: "Moody's",
		items: [
			{ label: "Rating", value: "Aa2" },
			{ label: "Outlook", value: "Stable" },
		],
	},
	{
		agency: "Fitch",
		fullAgency: "Fitch",
		items: [
			{ label: "Rating", value: "AA-" },
			{ label: "Outlook", value: "Stable" },
		],
	},
]);

const pairs = buildCreditRatingPairs({
	label: "Credit rating",
	visualization: {
		left: { raw: leftRaw },
		right: { raw: rightRaw },
	},
});

assert.strictEqual(pairs.length, 3);
assert.strictEqual(pairs[0].agency, "S&P");
assert.deepStrictEqual(pairs[0].left.items.map(item => item.value), ["AA-", "AA-", "AA", "Stable"]);
assert.deepStrictEqual(pairs[0].right.items.map(item => item.value), ["A+", "A+", "AA+", "Stable"]);
assert.strictEqual(pairs[1].left.items[0].label, "Rating");
assert.strictEqual(pairs[2].right.items[0].value, "A");

console.log("creditRatingDisplay tests passed");
