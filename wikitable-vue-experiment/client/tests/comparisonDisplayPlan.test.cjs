const assert = require("assert");

const {
	buildComparisonDisplayPlan,
	normalizeDisplayLabel,
} = require("../src/js/comparisonDisplayPlan.js");

assert.strictEqual(normalizeDisplayLabel("  PPP "), "ppp");
assert.strictEqual(normalizeDisplayLabel("United States"), "united states");
assert.strictEqual(normalizeDisplayLabel("GDP-growth"), "gdp growth");
assert.strictEqual(normalizeDisplayLabel("Côte d’Ivoire"), "côte d ivoire");

const fdiPlan = buildComparisonDisplayPlan({
	label: "FDI stock",
	visualization: {
		left: {
			values: [
				{ label: "Inward", display: "Inward (2017): $230.6 billion" },
				{ label: "Abroad", display: "Abroad (2017): $33.67 billion" },
			],
		},
		right: {
			values: [
				{ label: "Inward", display: "Inward (2022): $367.8 billion" },
				{ label: "Outward", display: "Outward (2022): $171.2 billion" },
			],
		},
	},
});

assert.deepStrictEqual(fdiPlan.left, [
	{
		label: "Inward",
		valueText: "$230.6 billion",
		shared: true,
		colorKey: "shared-0",
		key: "shared-inward",
	},
	{
		label: "Abroad",
		valueText: "$33.67 billion",
		shared: false,
		colorKey: "unmatched-left-0",
		key: "left-abroad",
	},
]);
assert.deepStrictEqual(fdiPlan.right, [
	{
		label: "Inward",
		valueText: "$367.8 billion",
		shared: true,
		colorKey: "shared-0",
		key: "shared-inward",
	},
	{
		label: "Outward",
		valueText: "$171.2 billion",
		shared: false,
		colorKey: "unmatched-right-0",
		key: "right-outward",
	},
]);

const reorderedPlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			values: [
				{ label: "nominal", display: "nominal: $1.8 trillion" },
				{ label: "PPP", display: "PPP: $3.1 trillion" },
			],
		},
		right: {
			values: [
				{ label: "PPP", display: "PPP: $6.7 trillion" },
				{ label: "nominal", display: "nominal: $4.2 trillion" },
			],
		},
	},
});

assert.deepStrictEqual(
	reorderedPlan.left.map(item => item.label),
	["nominal", "PPP"]
);
assert.deepStrictEqual(
	reorderedPlan.right.map(item => item.label),
	["nominal", "PPP"]
);

const singlePlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			raw: "Seoul",
			values: [{ display: "Seoul" }],
		},
		right: {
			raw: "Tokyo",
			values: [{ value: "Tokyo" }],
		},
	},
});

assert.deepStrictEqual(singlePlan.left, [
	{ label: "", valueText: "Seoul", shared: false, colorKey: "single", key: "single" },
]);
assert.deepStrictEqual(singlePlan.right, [
	{ label: "", valueText: "Tokyo", shared: false, colorKey: "single", key: "single" },
]);

const rawUnitPlan = buildComparisonDisplayPlan({
	dataType: "Numerical",
	visualization: {
		left: {
			raw: "$542.4 billion (2020)",
			values: [{ value: 542400000000, year: 2020 }],
		},
		right: {
			raw: "$4.54 trillion (March 2023) (103.2% of GDP)",
			values: [{ value: 4540000000000, year: 2023 }],
		},
	},
});
assert.deepStrictEqual(rawUnitPlan.left, [
	{ label: "", valueText: "$542.4 billion", shared: false, colorKey: "single", key: "single" },
]);
assert.deepStrictEqual(rawUnitPlan.right, [
	{ label: "", valueText: "$4.54 trillion", shared: false, colorKey: "single", key: "single" },
]);

const zeroValuePlan = buildComparisonDisplayPlan({
	visualization: {
		left: { values: [{ label: "Balance", value: 0 }] },
		right: { values: [{ label: "Balance", display: "Balance: 0" }] },
	},
});
assert.deepStrictEqual(zeroValuePlan.left, [
	{ label: "", valueText: "0", shared: false, colorKey: "single", key: "single" },
]);
assert.deepStrictEqual(zeroValuePlan.right, [
	{ label: "", valueText: "0", shared: false, colorKey: "single", key: "single" },
]);

const duplicateLabelPlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			values: [
				{ label: "A", display: "A: 10" },
				{ label: "A", display: "A: 20" },
			],
		},
		right: {
			values: [
				{ label: "A", display: "A: 11" },
				{ label: "A", display: "A: 21" },
			],
		},
	},
});
assert.deepStrictEqual(
	duplicateLabelPlan.left.map(item => item.key),
	["shared-a-0", "shared-a-1"]
);
assert.deepStrictEqual(
	duplicateLabelPlan.right.map(item => item.key),
	["shared-a-0", "shared-a-1"]
);
assert.deepStrictEqual(
	duplicateLabelPlan.left.map(item => item.colorKey),
	["shared-0", "shared-1"]
);

const unmatchedDuplicatePlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			values: [
				{ label: "A", display: "A: 10" },
				{ label: "A", display: "A: 20" },
			],
		},
		right: {
			values: [
				{ label: "B", display: "B: 11" },
				{ label: "C", display: "C: 21" },
			],
		},
	},
});
assert.deepStrictEqual(
	unmatchedDuplicatePlan.left.map(item => item.key),
	["left-a-0", "left-a-1"]
);

const positionalPlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			values: [
				{ display: "Electronics" },
				{ display: "Cars" },
			],
		},
		right: {
			values: [
				{ display: "Steel" },
				{ display: "Robotics" },
			],
		},
	},
});

assert.deepStrictEqual(
	positionalPlan.left.map(item => item.label),
	["1", "2"]
);
assert.deepStrictEqual(
	positionalPlan.right.map(item => item.label),
	["1", "2"]
);

const structuredPlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			structuredValues: [
				{ label: "Name", value: "South Korean won" },
				{ label: "Code", value: "KRW" },
				{ label: "Symbol", value: "₩" },
			],
		},
		right: {
			structuredValues: [
				{ label: "Name", value: "Japanese yen" },
				{ label: "Code", value: "JPY" },
				{ label: "Symbol", value: "¥" },
			],
		},
	},
});

assert.deepStrictEqual(
	structuredPlan.left.map(item => `${item.label}: ${item.valueText} ${item.colorKey}`),
	["Name: South Korean won shared-0", "Code: KRW shared-1", "Symbol: ₩ shared-2"]
);
assert.deepStrictEqual(
	structuredPlan.right.map(item => `${item.label}: ${item.valueText} ${item.colorKey}`),
	["Name: Japanese yen shared-0", "Code: JPY shared-1", "Symbol: ¥ shared-2"]
);

const listStructuredPlan = buildComparisonDisplayPlan({
	visualization: {
		left: {
			structuredValues: [
				{ label: "Electronics", value: "Electronics" },
				{ label: "Shipbuilding", value: "Shipbuilding" },
			],
		},
		right: {
			structuredValues: [
				{ label: "Electronics", value: "Electronics" },
				{ label: "Steel", value: "Steel" },
			],
		},
	},
});
assert.deepStrictEqual(
	listStructuredPlan.left.map(item => `${item.label}|${item.valueText}`),
	["|Electronics", "|Shipbuilding"]
);
assert.deepStrictEqual(
	listStructuredPlan.right.map(item => `${item.label}|${item.valueText}`),
	["|Electronics", "|Steel"]
);

const oneSidedPlan = buildComparisonDisplayPlan({
	visualization: {
		left: { raw: "Available", values: [] },
		right: { raw: "", values: [] },
	},
});
assert.deepStrictEqual(oneSidedPlan.left, [
	{ label: "", valueText: "Available", shared: false, colorKey: "single", key: "single" },
]);
assert.deepStrictEqual(oneSidedPlan.right, [
	{ label: "", valueText: "—", shared: false, colorKey: "single", key: "single" },
]);

console.log("comparisonDisplayPlan tests passed");
