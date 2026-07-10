const assert = require("assert");

const {
	buildCompactProportionalRows,
	buildCompactValueRows,
} = require("../src/js/proportionalPreview.js");

const rows = buildCompactProportionalRows([
	{ label: "Integrated circuits", value: 15.35, display: "Integrated circuits (2019): 15.35%" },
	{ label: "Machinery", value: 12.81, display: "12.81%" },
	{ label: "Vehicles and their parts", value: 11.34, display: "11.34%" },
	{ label: "Mineral fuels", value: 7.01, display: "7.01%" },
	{ label: "Plastics", value: 5.86, display: "5.86%" },
	{ label: "Iron and steel", value: 4.23, display: "4.23%" },
]);

assert.deepStrictEqual(
	rows.map(row => ({
		label: row.label,
		valueText: row.valueText,
		isMore: row.isMore,
	})),
		[
			{ label: "Integrated circuits", valueText: "15.35%", isMore: false },
			{ label: "Machinery", valueText: "12.81%", isMore: false },
			{ label: "Vehicles and their parts", valueText: "11.34%", isMore: false },
		{ label: "Mineral fuels", valueText: "7.01%", isMore: false },
		{ label: "Plastics", valueText: "5.86%", isMore: false },
		{ label: "+ 1 more", valueText: "", isMore: true },
	]
);

const sourceOrderedRows = buildCompactProportionalRows([
	{ label: "Agriculture", value: 1.6, display: "Agriculture (2023): 1.6%" },
	{ label: "Industry", value: 31.6, display: "Industry (2023): 31.6%" },
	{ label: "Services", value: 58.4, display: "Services (2023): 58.4%" },
]);

assert.deepStrictEqual(
	sourceOrderedRows.map(row => `${row.label}=${row.valueText}`),
	[
		"Agriculture=1.6%",
		"Industry=31.6%",
		"Services=58.4%",
	]
);

const compactValueRows = buildCompactValueRows([
	{ label: "nominal", value: 1870000000000, display: "nominal (2025): $1.87 trillion" },
	{ label: "PPP", value: 3360000000000, display: "PPP (2025): $3.36 trillion" },
]);

assert.deepStrictEqual(
	compactValueRows.map(row => `${row.label}=${row.valueText}`),
	[
		"nominal=$1.87 trillion",
		"PPP=$3.36 trillion",
	]
);

const yearOnlyRows = buildCompactValueRows([
	{ label: "2025: 1.0%", value: 1, display: "2025: 1.0%" },
	{ label: "2026: 1.4%", value: 1.4, display: "2026: 1.4%" },
]);

assert.deepStrictEqual(
	yearOnlyRows.map(row => `${row.label}=${row.valueText}`),
	[
		"2025=1.0%",
		"2026=1.4%",
	]
);

console.log("proportionalPreview tests passed");
