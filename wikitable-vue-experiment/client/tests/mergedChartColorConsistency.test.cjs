const assert = require("assert");
const { buildMergedComparison } = require("../src/js/mergedComparisonData.js");
const { buildMergedComparisonOption, buildMergedAdaptiveState } = require("../src/js/mergedComparisonAdaptiveOptions.js");

const rowLevelColors = {
	China: "#111111",
	"United States": "#222222",
	Others: "#333333",
};

const row = {
	label: "Main import partners",
	dataType: "Proportional",
	mergeVisualization: "pie-chart",
	categoryColors: rowLevelColors,
	visualization: {
		left: {
			raw: "China 23.2% United States 10.1% Others 66.7%",
			values: [
				{ value: 23.2, label: "China", raw: "China 23.2%" },
				{ value: 10.1, label: "United States", raw: "United States 10.1%" },
				{ value: 66.7, label: "Others", raw: "Others 66.7%" },
			],
		},
		right: {
			raw: "China 19.9% United States 8.4% Others 71.7%",
			values: [
				{ value: 19.9, label: "China", raw: "China 19.9%" },
				{ value: 8.4, label: "United States", raw: "United States 8.4%" },
				{ value: 71.7, label: "Others", raw: "Others 71.7%" },
			],
		},
	},
};

const merged = buildMergedComparison(row, { left: "Left article", right: "Right article" });
assert.strictEqual(merged.mode, "stacked");
assert.strictEqual(
	merged.categoryColors.China,
	rowLevelColors.China,
	"Merged comparison data should preserve the same row-level color used by thumbnails/full side charts"
);
assert.strictEqual(merged.categoryColors["United States"], rowLevelColors["United States"]);
assert.strictEqual(merged.categoryColors.Others, rowLevelColors.Others);

const state = buildMergedAdaptiveState({ data: merged });
const option = buildMergedComparisonOption({ data: merged, state, grid: {} });
const colorBySeriesName = Object.fromEntries(option.series.map(series => [series.name, series.itemStyle.color]));
assert.deepStrictEqual(
	colorBySeriesName,
	rowLevelColors,
	"Merged chart rendered series colors should exactly match the thumbnail/full-chart row palette"
);

console.log("mergedChartColorConsistency tests passed");
