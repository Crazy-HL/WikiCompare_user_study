const assert = require("assert");
const { buildMergedComparison } = require("../src/js/mergedComparisonData.js");
const { PAPER_PIE_COLORS, FALLBACK_CATEGORY_COLORS } = require("../src/js/chartTheme.js");

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
	assert.deepStrictEqual(merged.scaleContext.leftValues, [1.4, 2, 1]);
	assert.deepStrictEqual(merged.scaleContext.rightValues, [1.5, 0.8, 0.6]);
	assert.deepStrictEqual(merged.scaleContext.domain, merged.yDomain);
	assert.strictEqual(merged.scaleContext.visualization, "line-chart");
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
	assert.deepStrictEqual(merged.series[0].data.map(point => point.value), [22.5, 11.6]);
	assert.deepStrictEqual(merged.series[1].data.map(point => point.value), [19.2, 18.3]);
});

test("keeps non-year categories in comparison order instead of alphabetical order", () => {
	const row = {
		label: "FDI stock",
		dataType: "Numerical",
		mergeVisualization: "bar-chart",
		visualization: {
			left: {
				raw: "$230.6 billion (2017) Abroad: $344.7 billion (2017)",
				values: [
					{ value: 230600000000, label: "Inward", year: 2017 },
					{ value: 344700000000, label: "Abroad", year: 2017 },
				],
			},
			right: {
				raw: "Inward: $25 billion (2021) Outward: $147 billion (2021)",
				values: [
					{ value: 25000000000, label: "Inward", year: 2021 },
					{ value: 147000000000, label: "Outward", year: 2021 },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.deepStrictEqual(merged.categories, ["Inward", "Abroad", "Outward"]);
	assert.strictEqual(merged.series[0].data[2].value, null);
	assert.strictEqual(merged.series[1].data[1].value, null);
});

test("preserves stacked source semantics for proportional comparisons", () => {
	const row = {
		label: "Export goods",
		dataType: "Proportional",
		mergeVisualization: "stacked-chart",
		visualization: {
			left: {
				raw: "Machinery 12.8% Mineral fuels 7.0%",
				values: [
					{ value: 12.8, label: "Machinery" },
					{ value: 7.0, label: "Mineral fuels" },
				],
			},
			right: {
				raw: "Machinery 19.9% Chemicals 12.4%",
				values: [
					{ value: 19.9, label: "Machinery" },
					{ value: 12.4, label: "Chemicals" },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "stacked");
	assert.deepStrictEqual(merged.categories, ["Machinery", "Mineral fuels", "Chemicals"]);
	assert.strictEqual(merged.scaleContext.visualization, "stacked-chart");
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
	assert.strictEqual(merged.unit, "%");
	assert.strictEqual(merged.basis, "GDP");
	assert.deepStrictEqual(merged.yDomain, [-6.82, 6.82]);
	assert.strictEqual(merged.stats.deltaDisplay, "3.5%");
	assert.strictEqual(merged.series[1].data[0].display, "-6.2% of GDP");
	assert.deepStrictEqual(merged.scaleContext.leftValues, [-2.7]);
	assert.deepStrictEqual(merged.scaleContext.rightValues, [-6.2]);
	assert.deepStrictEqual(merged.scaleContext.domain, merged.yDomain);
	assert.strictEqual(merged.scaleContext.visualization, "bar-chart");
});

test("keeps forced-bar single negative and zero points when their shared label collapses to the row label", () => {
	const row = {
		label: "Budget balance",
		dataType: "Proportional",
		mergeVisualization: "bar-chart",
		visualization: {
			left: {
				raw: "-2.7% of GDP",
				values: [{ value: -2.7, label: "% of GDP" }],
			},
			right: {
				raw: "0% of GDP",
				values: [{ value: 0, label: "% of GDP" }],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "bar");
	assert.deepStrictEqual(merged.categories, ["Budget balance"]);
	assert.strictEqual(merged.series[0].data[0].value, -2.7);
	assert.strictEqual(merged.series[1].data[0].value, 0);
	assert.strictEqual(merged.series[0].data[0].display, "-2.7% of GDP");
	assert.strictEqual(merged.series[1].data[0].display, "0.0% of GDP");
	assert.deepStrictEqual(merged.scaleContext.leftValues, [-2.7]);
	assert.deepStrictEqual(merged.scaleContext.rightValues, [0]);
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

test("matches a numerical currency display to point.value instead of an incidental percentage", () => {
	const row = {
		label: "Spending",
		dataType: "Numerical",
		visualization: {
			left: {
				raw: "$456.5 billion (2020)",
				values: [{ value: 456500000000, year: 2020 }],
			},
			right: {
				raw: "¥239,694 billion 43.4% of GDP (2022)",
				values: [{ value: 239694000000000, year: 2022 }],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);
	const rightPoint = merged.series[1].data[1];

	assert.strictEqual(rightPoint.value, 239694000000000);
	assert.strictEqual(rightPoint.display, "¥239,694 billion");
	assert.deepStrictEqual(merged.scaleContext.rightValues, [239694000000000]);
	assert.deepStrictEqual(merged.scaleContext.domain, merged.yDomain);
});

test("does not format body-text sales counts as percentages when market share is present", () => {
	const row = {
		label: "Annual sales",
		dataType: "Numerical",
		visualization: {
			left: {
				raw: "Sales in 2023 totaled 7.4 million units with a market share of 30.2%.",
				values: [{ value: 7400000, year: 2023, label: "sales" }],
			},
			right: {
				raw: "Sales totaled 1,402,371 units in 2023, with a market share of 9.1%.",
				values: [{ value: 1402371, year: 2023, label: "sales" }],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.unit, "");
	assert.strictEqual(merged.series[0].data[0].display, "7.4 million");
	assert.strictEqual(merged.series[1].data[0].display, "1,402,371");
});

test("sanitizes stale year-only display values for merged chart labels", () => {
	const row = {
		label: "Exports",
		dataType: "Numerical",
		mergeVisualization: "line-chart",
		visualization: {
			left: {
				raw: "exports: $814.9 billion (2024 est.)",
				values: [
					{
						value: 814900000000,
						year: 2024,
						label: "Exports 2024",
						display: "Exports 2024 (2024): 2024",
					},
				],
			},
			right: {
				raw: "exports: $268.6 billion (2024 est.)",
				values: [
					{
						value: 268600000000,
						year: 2024,
						label: "Exports 2024",
						display: "Exports 2024 (2024): 2024",
					},
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.series[0].data[0].display, "814.9B");
	assert.strictEqual(merged.series[1].data[0].display, "268.6B");
});

test("excludes aggregate total from alcohol component comparison categories", () => {
	const row = {
		label: "Alcohol consumption per capita",
		dataType: "Numerical",
		visualization: {
			left: {
				raw: "total: 3.09 liters of pure alcohol beer: 0.23 liters of pure alcohol wine: 0 liters of pure alcohol spirits: 2.85 liters of pure alcohol",
				values: [
					{ value: 3.09, label: "total", rawText: "3.09 liters of pure alcohol" },
					{ value: 0.23, label: "beer", rawText: "0.23 liters of pure alcohol" },
					{ value: 0, label: "wine", rawText: "0 liters of pure alcohol" },
					{ value: 2.85, label: "spirits", rawText: "2.85 liters of pure alcohol" },
				],
			},
			right: {
				raw: "total: 0.08 liters of pure alcohol beer: 0.06 liters of pure alcohol wine: 0.01 liters of pure alcohol spirits: 0.02 liters of pure alcohol",
				values: [
					{ value: 0.08, label: "total", rawText: "0.08 liters of pure alcohol" },
					{ value: 0.06, label: "beer", rawText: "0.06 liters of pure alcohol" },
					{ value: 0.01, label: "wine", rawText: "0.01 liters of pure alcohol" },
					{ value: 0.02, label: "spirits", rawText: "0.02 liters of pure alcohol" },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.deepStrictEqual(merged.categories, ["beer", "wine", "spirits"]);
	assert.strictEqual(merged.unit, "liters of pure alcohol per capita");
	assert.strictEqual(merged.mode, "bar");
});

test("keeps empty aligned values out of the shared scale context", () => {
	const row = {
		label: "Sparse yearly values",
		dataType: "Trend",
		mergeVisualization: "line-chart",
		visualization: {
			left: {
				raw: "No value for 2020; 2 in 2021",
				values: [
					{ value: null, year: 2020 },
					{ value: 2, year: 2021 },
				],
			},
			right: {
				raw: "10 in 2020; no value for 2021",
				values: [
					{ value: 10, year: 2020 },
					{ value: undefined, year: 2021 },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.series[0].data[0].value, null);
	assert.strictEqual(merged.series[1].data[1].value, null);
	assert.deepStrictEqual(merged.scaleContext.leftValues, [2]);
	assert.deepStrictEqual(merged.scaleContext.rightValues, [10]);
});

test("uses stacked composition for pie-origin merged comparison", () => {
	const row = {
		label: "Main import partners",
		dataType: "Proportional",
		mergeVisualization: "pie-chart",
		visualization: {
			left: {
				raw: "China: 24%, United States: 12%, Other: 64%",
				values: [
					{ value: 24, label: "China", rawText: "China: 24%" },
					{ value: 12, label: "United States", rawText: "United States: 12%" },
					{ value: 64, label: "Other", rawText: "Other: 64%" },
				],
			},
			right: {
				raw: "China: 18%, Germany: 10%, Other: 72%",
				values: [
					{ value: 18, label: "China", rawText: "China: 18%" },
					{ value: 10, label: "Germany", rawText: "Germany: 10%" },
					{ value: 72, label: "Other", rawText: "Other: 72%" },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "stacked");
	assert.deepStrictEqual(merged.categories, ["China", "Other", "United States", "Germany"]);
	assert.strictEqual(merged.scaleContext.visualization, "stacked-chart");
	assert.strictEqual(merged.scaleContext.adaptiveEligible, false);
	assert.strictEqual(merged.categoryColors.China, PAPER_PIE_COLORS[0]);
	assert.strictEqual(merged.categoryColors.Other, PAPER_PIE_COLORS[2]);
});

test("keeps stacked-origin merged composition category colors frozen across both sides", () => {
	const row = {
		label: "Exports",
		dataType: "Proportional",
		mergeVisualization: "stacked-chart",
		visualization: {
			left: {
				raw: "Machinery: 40%, Vehicles: 20%",
				values: [
					{ value: 40, label: "Machinery" },
					{ value: 20, label: "Vehicles" },
				],
			},
			right: {
				raw: "Machinery: 35%, Chemicals: 15%",
				values: [
					{ value: 35, label: "machinery" },
					{ value: 15, label: "Chemicals" },
				],
			},
		},
	};

	const merged = buildMergedComparison(row, titles);

	assert.strictEqual(merged.mode, "stacked");
	assert.deepStrictEqual(merged.categories, ["Machinery", "Vehicles", "Chemicals"]);
	assert.strictEqual(merged.categoryColors.Machinery, FALLBACK_CATEGORY_COLORS[0]);
	assert.strictEqual(merged.categoryColors.Vehicles, FALLBACK_CATEGORY_COLORS[1]);
	assert.strictEqual(merged.categoryColors.Chemicals, FALLBACK_CATEGORY_COLORS[2]);
});
