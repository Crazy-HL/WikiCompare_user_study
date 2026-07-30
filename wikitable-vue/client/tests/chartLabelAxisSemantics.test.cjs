const assert = require("assert");
const fs = require("fs");
const path = require("path");

const simpleChartSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "SimpleChart.vue"),
	"utf8"
);
const compareTableSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);
const mergedChartComponentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "MergedComparisonChart.vue"),
	"utf8"
);
const mergedChartOptionSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "mergedComparisonAdaptiveOptions.js"),
	"utf8"
);
const mergedChartSource = `${mergedChartComponentSource}
${mergedChartOptionSource}`;
const fullChartComponentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "FullChart.vue"),
	"utf8"
);
const fullChartOptionSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "fullChartAdaptiveOptions.js"),
	"utf8"
);
const fullChartSource = `${fullChartComponentSource}
${fullChartOptionSource}`;
const legacyChartSources = ["BarChart.vue", "LineChart.vue", "CombinedChart.vue"].map(file =>
	fs.readFileSync(
		path.join(__dirname, "..", "src", "components", "compoents_base", "charts", file),
		"utf8"
	)
);

assert(
	!compareTableSource.includes("label: value.label || valueDisplayText"),
	"CompareTable should not turn formatted value text into chart labels"
);

assert(
	simpleChartSource.includes("categoryLabelForPoint") &&
		simpleChartSource.includes("categoryLabel:"),
	"SimpleChart should compute category labels separately from value displays"
);

assert(
	!simpleChartSource.includes(".text(d => compactSvgText(d.categoryLabel") &&
		simpleChartSource.includes('attr("class", "bar-value-label")'),
	"SimpleChart bar previews should not render category x-axis labels in the three-column table"
);

assert(
	!simpleChartSource.includes("renderYAxis") &&
		!simpleChartSource.includes(".attr(\"class\", \"y-axis-tick\")") &&
		!simpleChartSource.includes(".attr(\"class\", \"y-axis-grid\")"),
	"SimpleChart previews should omit vertical-axis ticks and gridlines in the three-column table"
);

assert(
	mergedChartSource.includes("name: axisMeasureLabel(data)") &&
		mergedChartSource.includes("nameLocation: \"middle\""),
	"MergedComparisonChart should display inferred y-axis measurement context instead of calling GDP share a unit"
);

assert(
	fullChartSource.includes("name: axisUnitLabel ||") &&
		fullChartSource.includes("liters of pure alcohol per capita"),
	"FullChart should display inferred y-axis units for non-percent measurements"
);

assert(
	mergedChartSource.includes("splitNumber: AXIS_SPLIT_NUMBER") &&
		mergedChartSource.includes("formatAxisNumber(number,") &&
		fullChartSource.includes("splitNumber: AXIS_SPLIT_NUMBER") &&
		fullChartSource.includes("formatAxisNumber(value, {"),
	"Full-size and merged chart y-axes should use tick-aware numeric formatting so close ticks do not collapse to the same label"
);

assert(
	legacyChartSources.every(source =>
		source.includes("formatAxisNumber") &&
			source.includes("splitNumber: AXIS_SPLIT_NUMBER")
	),
	"Legacy chart components should use the shared tick-aware axis formatter too"
);

assert(
	simpleChartSource.includes("previewDisplayText") &&
		simpleChartSource.includes("shortValueText(item, props.type)"),
	"SimpleChart should keep typed display formatting as a fallback when preview labels are not unit-normalized"
);

assert(
	compareTableSource.includes("normalizePreviewChartItems") &&
		compareTableSource.includes("chartField(row, 'left', true)") &&
		compareTableSource.includes("chartField(row, 'right', true)") &&
		compareTableSource.includes("normalizedRowPreviewValues(row)"),
	"CompareTable side previews should normalize chart units before rendering the small three-column charts"
);

assert(
	simpleChartSource.includes("normalizePreviewChartItems") &&
		simpleChartSource.includes("normalizedPreviewField") &&
		simpleChartSource.includes("item?.stripPreviewUnit") &&
		simpleChartSource.includes("item.unitlessDisplay"),
	"SimpleChart previews should use unitless compact labels once chart values are normalized"
);

console.log("chartLabelAxisSemantics tests passed");
