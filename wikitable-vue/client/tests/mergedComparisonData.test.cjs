const assert = require("assert");
const { buildMergedComparison } = require("../src/js/mergedComparisonData.js");

function test(name, fn) {
	try {
		fn();
		console.log(`ok - ${name}`);
	} catch (error) {
		console.error(`not ok - ${name}`);
		throw error;
	}
}

const titles = { left: "South Korea", right: "Japan" };

test("uses a line comparison for shared yearly series", () => {
	const row = {
		label: "GDP growth",
		dataType: "Trend",
		mergeVisualization: "line-chart",
		visualization: {
			left: {
				raw: "1.4% (2023) 2.0% (2024) 1.0% (2025)",
				values: [
					{ value: 1.4, year: 2023 },
					{ value: 2.0, year: 2024 },
					{ value: 1.0, year: 2025 },
				],
			},
			right: {
				raw: "1.5% (2023) 0.8% (2024) 0.6% (2025)",
				values: [
					{ value: 1.5, year: 2023 },
					{ value: 0.8, year: 2024 },
					{ value: 0.6, year: 2025 },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "line");
	assert.deepStrictEqual(merged.categories, ["2023", "2024", "2025"]);
	assert.strictEqual(merged.series[0].name, "South Korea");
	assert.strictEqual(merged.series[1].data[1].display, "0.8%");
});

test("keeps merged chart as bars when both side charts are bars", () => {
	const row = {
		label: "GDP growth",
		dataType: "Trend",
		mergeVisualization: "bar-chart",
		visualization: {
			left: {
				raw: "1.4% (2023) 2.0% (2024)",
				values: [
					{ value: 1.4, year: 2023 },
					{ value: 2.0, year: 2024 },
				],
			},
			right: {
				raw: "1.5% (2023) 0.8% (2024)",
				values: [
					{ value: 1.5, year: 2023 },
					{ value: 0.8, year: 2024 },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "bar");
	assert.deepStrictEqual(merged.categories, ["2023", "2024"]);
});

test("uses grouped bars for matching labeled categories", () => {
	const row = {
		label: "Main export partners",
		dataType: "Proportional",
		visualization: {
			left: {
				raw: "China 22.5% United States 11.6%",
				values: [
					{ value: 22.5, label: "China" },
					{ value: 11.6, label: "United States" },
				],
			},
			right: {
				raw: "China 19.2% United States 18.3%",
				values: [
					{ value: 19.2, label: "China" },
					{ value: 18.3, label: "United States" },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "bar");
	assert.deepStrictEqual(merged.categories, ["China", "United States"]);
	assert.strictEqual(merged.unit, "%");
	assert.strictEqual(merged.series[0].data[0].display, "22.5%");
});

test("keeps single negative values readable on a symmetric axis", () => {
	const row = {
		label: "Budget balance",
		dataType: "Proportional",
		visualization: {
			left: {
				raw: "-2.7% of GDP",
				values: [{ value: -2.7, label: "% of GDP" }],
			},
			right: {
				raw: "-6.2% of GDP",
				values: [{ value: -6.2, label: "% of GDP" }],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "single");
	assert.deepStrictEqual(merged.categories, ["Budget balance"]);
	assert.deepStrictEqual(merged.yDomain, [-6.82, 6.82]);
	assert.strictEqual(merged.stats.deltaDisplay, "3.5%");
	assert.strictEqual(merged.series[1].data[0].display, "-6.2% of GDP");
});

test("prefers currency axis for numerical money values with incidental GDP percentages", () => {
	const row = {
		label: "Gross external debt",
		dataType: "Numerical",
		visualization: {
			left: {
				raw: "$542.4 billion (2020)",
				values: [{ value: 542400000000, year: 2020, raw: "$542.4 billion (2020)" }],
			},
			right: {
				raw: "$4.54 trillion (March 2023) (103.2% of GDP)",
				values: [{ value: 4540000000000, year: 2023, raw: "$4.54 trillion (March 2023) (103.2% of GDP)" }],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.unit, "USD");
	assert.strictEqual(merged.stats.deltaDisplay, "4T");
});
