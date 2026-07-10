const assert = require("assert");

const {
	buildStructuredListItems,
	hasStructuredValues,
} = require("../src/js/structuredValueDisplay.js");

const row = {
	label: "Main industries",
	visualization: {
		left: {
			structuredValues: [
				{ label: "Electronics", value: "Electronics", kind: "list_item" },
				{ label: "Telecommunications", value: "Telecommunications", kind: "list_item" },
				{ label: "Shipbuilding", value: "Shipbuilding", kind: "list_item" },
			],
		},
		right: {
			structuredValues: [
				{ label: "High technology", value: "High technology", kind: "list_item" },
				{ label: "Electronics", value: "Electronics", kind: "list_item" },
				{ label: "Steel", value: "Steel", kind: "list_item" },
			],
		},
	},
};

assert.strictEqual(hasStructuredValues(row), true);
assert.deepStrictEqual(buildStructuredListItems(row, "left"), [
	{ label: "Electronics", value: "Electronics", display: "Electronics", kind: "list_item", hasDistinctLabel: false, shared: true },
	{ label: "Telecommunications", value: "Telecommunications", display: "Telecommunications", kind: "list_item", hasDistinctLabel: false, shared: false },
	{ label: "Shipbuilding", value: "Shipbuilding", display: "Shipbuilding", kind: "list_item", hasDistinctLabel: false, shared: false },
]);
assert.deepStrictEqual(buildStructuredListItems(row, "right"), [
	{ label: "High technology", value: "High technology", display: "High technology", kind: "list_item", hasDistinctLabel: false, shared: false },
	{ label: "Electronics", value: "Electronics", display: "Electronics", kind: "list_item", hasDistinctLabel: false, shared: true },
	{ label: "Steel", value: "Steel", display: "Steel", kind: "list_item", hasDistinctLabel: false, shared: false },
]);

const currencyRow = {
	label: "Currency",
	visualization: {
		left: {
			structuredValues: [
				{ label: "Name", value: "South Korean won", kind: "entity_name" },
				{ label: "Code", value: "KRW", kind: "currency_code" },
				{ label: "Symbol", value: "₩", kind: "currency_symbol" },
			],
		},
		right: {
			structuredValues: [
				{ label: "Name", value: "Japanese yen", kind: "entity_name" },
				{ label: "Code", value: "JPY", kind: "currency_code" },
				{ label: "Symbol", value: "¥", kind: "currency_symbol" },
			],
		},
	},
};

assert.deepStrictEqual(buildStructuredListItems(currencyRow, "left"), [
	{ label: "Name", value: "South Korean won", display: "Name: South Korean won", kind: "entity_name", hasDistinctLabel: true, shared: false },
	{ label: "Code", value: "KRW", display: "Code: KRW", kind: "currency_code", hasDistinctLabel: true, shared: false },
	{ label: "Symbol", value: "₩", display: "Symbol: ₩", kind: "currency_symbol", hasDistinctLabel: true, shared: false },
]);

console.log("structuredValueDisplay tests passed");
