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

const orderRow = {
	label: "Stack order comparison",
	dataType: "Proportional",
	mergeVisualization: "stacked-chart",
	categoryColors: {
		Alpha: "#aa0000",
		Beta: "#00aa00",
		Gamma: "#8b4513",
	},
	visualization: {
		left: {
			raw: "Alpha 20% Beta 30% Gamma 50%",
			values: [
				{ value: 20, label: "Alpha", raw: "Alpha 20%" },
				{ value: 30, label: "Beta", raw: "Beta 30%" },
				{ value: 50, label: "Gamma", raw: "Gamma 50%" },
			],
		},
		right: {
			raw: "Gamma 15% Beta 25% Alpha 60%",
			values: [
				{ value: 15, label: "Gamma", raw: "Gamma 15%" },
				{ value: 25, label: "Beta", raw: "Beta 25%" },
				{ value: 60, label: "Alpha", raw: "Alpha 60%" },
			],
		},
	},
};

const orderMerged = buildMergedComparison(orderRow, { left: "Left", right: "Right" });
const orderState = buildMergedAdaptiveState({ data: orderMerged });
const orderOption = buildMergedComparisonOption({ data: orderMerged, state: orderState, grid: {} });
const stackOrderForAxisIndex = axisIndex => orderOption.series
	.filter(series => series.data?.[axisIndex] && Number.isFinite(Number(series.data[axisIndex].value)))
	.map(series => series.name);
assert.deepStrictEqual(
	stackOrderForAxisIndex(0),
	["Alpha", "Beta", "Gamma"],
	"The left merged stacked bar should keep the same bottom-to-top category order as the left thumbnail/full chart"
);
assert.deepStrictEqual(
	stackOrderForAxisIndex(1),
	["Gamma", "Beta", "Alpha"],
	"The right merged stacked bar should keep the same bottom-to-top category order as the right thumbnail/full chart"
);
assert.strictEqual(
	orderOption.series.find(series => series.name === "Gamma" && series.data?.[0])?.itemStyle?.color,
	"#8b4513",
	"The top left merged segment should keep the thumbnail/full-chart color for Gamma"
);
assert.strictEqual(
	orderOption.series.find(series => series.name === "Alpha" && series.data?.[1])?.itemStyle?.color,
	"#aa0000",
	"The top right merged segment should keep the thumbnail/full-chart color for Alpha"
);

console.log("mergedChartColorConsistency tests passed");
