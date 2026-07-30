const assert = require("assert");

const {
	buildTextPairs,
	textItemFromRawPart,
	stripDisplayLabel,
} = require("../src/js/textComparisonDisplay.js");

const gdpRankRow = {
	dataType: "Ordinal",
	visualization: {
		left: {
			raw: "13th (nominal); 14th (PPP)",
			values: [
				{ value: 13, label: "nominal" },
				{ value: 14, label: "PPP" },
			],
		},
		right: {
			raw: "4th (nominal); 4th (PPP)",
			values: [
				{ value: 4, label: "nominal" },
				{ value: 4, label: "PPP" },
			],
		},
	},
};

const gdpRankPairs = buildTextPairs(gdpRankRow);
assert.strictEqual(gdpRankPairs.length, 2);
assert.deepStrictEqual(
	gdpRankPairs.map(pair => ({
		leftLabel: pair.left.displayLabel,
		rightLabel: pair.right.displayLabel,
		leftValue: pair.left.value,
		rightValue: pair.right.value,
		leftMarker: pair.left.markerText,
		rightMarker: pair.right.markerText,
		leftShowIndex: pair.left.showIndex,
		rightShowIndex: pair.right.showIndex,
	})),
	[
		{
			leftLabel: "nominal",
			rightLabel: "nominal",
			leftValue: "13th",
			rightValue: "4th",
			leftMarker: "nominal",
			rightMarker: "nominal",
			leftShowIndex: false,
			rightShowIndex: false,
		},
		{
			leftLabel: "PPP",
			rightLabel: "PPP",
			leftValue: "14th",
			rightValue: "4th",
			leftMarker: "PPP",
			rightMarker: "PPP",
			leftShowIndex: false,
			rightShowIndex: false,
		},
	]
);

const staleGdpRankPairs = buildTextPairs({
	dataType: "Ordinal",
	visualization: {
		left: {
			raw: "13th (nominal); 14th (PPP)",
			values: [{ value: 13 }, { value: 14 }],
		},
		right: {
			raw: "4th (nominal); 4th (PPP)",
			values: [{ value: 4 }, { value: 4 }],
		},
	},
});
assert.deepStrictEqual(
	staleGdpRankPairs.map(pair => ({
		leftLabel: pair.left.displayLabel,
		rightLabel: pair.right.displayLabel,
		leftValue: pair.left.value,
		rightValue: pair.right.value,
		leftMarker: pair.left.markerText,
		rightMarker: pair.right.markerText,
		leftShowIndex: pair.left.showIndex,
		rightShowIndex: pair.right.showIndex,
	})),
	[
		{
			leftLabel: "nominal",
			rightLabel: "nominal",
			leftValue: "13th",
			rightValue: "4th",
			leftMarker: "nominal",
			rightMarker: "nominal",
			leftShowIndex: false,
			rightShowIndex: false,
		},
		{
			leftLabel: "PPP",
			rightLabel: "PPP",
			leftValue: "14th",
			rightValue: "4th",
			leftMarker: "PPP",
			rightMarker: "PPP",
			leftShowIndex: false,
			rightShowIndex: false,
		},
	]
);

const adjacentGdpRankPairs = buildTextPairs({
	dataType: "Ordinal",
	visualization: {
		left: {
			raw: "14th (nominal; 2025) 14th (PPP; 2025)",
			values: [{ value: 14 }, { value: 14 }],
		},
		right: {
			raw: "4th (nominal; 2026 5th (PPP; 2026",
			values: [{ value: 4 }, { value: 5 }],
		},
	},
});
assert.deepStrictEqual(
	adjacentGdpRankPairs.map(pair => ({
		leftLabel: pair.left.displayLabel,
		rightLabel: pair.right.displayLabel,
		leftValue: pair.left.value,
		rightValue: pair.right.value,
	})),
	[
		{ leftLabel: "nominal", rightLabel: "nominal", leftValue: "14th", rightValue: "4th" },
		{ leftLabel: "PPP", rightLabel: "PPP", leftValue: "14th", rightValue: "5th" },
	]
);

assert.deepStrictEqual(textItemFromRawPart("Nominal: 13th"), {
	label: "Nominal",
	value: "13th",
});
assert.deepStrictEqual(textItemFromRawPart("14th (PPP)"), {
	label: "PPP",
	value: "14th",
});
assert.strictEqual(stripDisplayLabel("nominal: 13th", "nominal"), "13th");

const oneSidedLabelPairs = buildTextPairs({
	dataType: "Ordinal",
	visualization: {
		left: {
			raw: "13th (nominal); 14th (PPP)",
			values: [
				{ value: 13, label: "nominal" },
				{ value: 14, label: "PPP" },
			],
		},
		right: {
			raw: "4th; 4th",
			values: [],
		},
	},
});
assert.strictEqual(oneSidedLabelPairs[0].left.displayLabel, "nominal");
assert.strictEqual(oneSidedLabelPairs[0].right.displayLabel, "nominal");
assert.strictEqual(oneSidedLabelPairs[0].right.value, "4th");
assert.strictEqual(oneSidedLabelPairs[0].right.showIndex, false);

const mismatchedLabelPairs = buildTextPairs({
	dataType: "Ordinal",
	visualization: {
		left: {
			raw: "13th (nominal)",
			values: [{ value: 13, label: "nominal" }],
		},
		right: {
			raw: "4th (PPP)",
			values: [{ value: 4, label: "PPP" }],
		},
	},
});
assert.strictEqual(mismatchedLabelPairs[0].left.displayLabel, "nominal");
assert.strictEqual(mismatchedLabelPairs[0].right.displayLabel, "PPP");
assert.strictEqual(mismatchedLabelPairs[0].left.showIndex, false);
assert.strictEqual(mismatchedLabelPairs[0].right.showIndex, false);

const unlabeledPairs = buildTextPairs({
	dataType: "Text",
	visualization: {
		left: { raw: "Manufacturing; Services", values: [] },
		right: { raw: "Industry; Services", values: [] },
	},
});
assert.strictEqual(unlabeledPairs[0].left.displayLabel, "");
assert.strictEqual(unlabeledPairs[0].right.displayLabel, "");
assert.strictEqual(unlabeledPairs[0].left.markerText, "1");
assert.strictEqual(unlabeledPairs[0].right.markerText, "1");
assert.strictEqual(unlabeledPairs[0].left.showIndex, true);
assert.strictEqual(unlabeledPairs[0].right.showIndex, true);

const singleUnlabeledPair = buildTextPairs({
	dataType: "Text",
	visualization: {
		left: { raw: "Calendar year", values: [] },
		right: { raw: "1 April – 31 March", values: [] },
	},
});
assert.strictEqual(singleUnlabeledPair.length, 1);
assert.strictEqual(singleUnlabeledPair[0].left.markerText, "");
assert.strictEqual(singleUnlabeledPair[0].right.markerText, "");
assert.strictEqual(singleUnlabeledPair[0].left.showIndex, false);
assert.strictEqual(singleUnlabeledPair[0].right.showIndex, false);

const parentheticalCommaPairs = buildTextPairs({
	dataType: "Text",
	visualization: {
		left: { raw: "South Korean won (KRW, ₩)", values: [] },
		right: { raw: "Japanese yen (JPY, ¥)", values: [] },
	},
});
assert.strictEqual(parentheticalCommaPairs.length, 1);
assert.strictEqual(parentheticalCommaPairs[0].left.displayLabel, "KRW");
assert.strictEqual(parentheticalCommaPairs[0].right.displayLabel, "JPY");
assert.strictEqual(parentheticalCommaPairs[0].left.value, "South Korean won");
assert.strictEqual(parentheticalCommaPairs[0].right.value, "Japanese yen");

const creditRatingItems = buildTextPairs({
	dataType: "Text",
	visualization: {
		left: {
			raw: "Standard & Poor's: AA- (Domestic) AA- (Foreign) AA (T&C Assessment) Outlook: Stable Moody's: Aa2 Outlook: Stable Fitch: AA- Outlook: Stable",
			values: [],
		},
		right: {
			raw: "Standard & Poor's: A+ (Domestic) A+ (Foreign) AA+ (T&C Assessment) Outlook: Stable Moody's: A1 Outlook: Stable Fitch: A Outlook: Stable",
			values: [],
		},
	},
});
assert.deepStrictEqual(
	creditRatingItems.map(pair => ({
		leftLabel: pair.left.displayLabel,
		rightLabel: pair.right.displayLabel,
		leftValue: pair.left.value,
		rightValue: pair.right.value,
	})),
	[
		{
			leftLabel: "Standard & Poor's",
			rightLabel: "Standard & Poor's",
			leftValue: "AA- (Domestic) AA- (Foreign) AA (T&C Assessment) Outlook: Stable",
			rightValue: "A+ (Domestic) A+ (Foreign) AA+ (T&C Assessment) Outlook: Stable",
		},
		{
			leftLabel: "Moody's",
			rightLabel: "Moody's",
			leftValue: "Aa2 Outlook: Stable",
			rightValue: "A1 Outlook: Stable",
		},
		{
			leftLabel: "Fitch",
			rightLabel: "Fitch",
			leftValue: "AA- Outlook: Stable",
			rightValue: "A Outlook: Stable",
		},
	]
);

console.log("textComparisonDisplay tests passed");
