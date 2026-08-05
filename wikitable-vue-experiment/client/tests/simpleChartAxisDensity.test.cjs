const assert = require("assert");
const fs = require("fs");
const path = require("path");
const {
	previewLabelIndexes,
	shouldShowPreviewLabel,
} = require("../src/js/chartValueDisplay");

const simpleChartSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "SimpleChart.vue"),
	"utf8"
);

assert.deepStrictEqual(
	previewLabelIndexes(5, 170, { maxVisible: 3 }),
	[0, 2, 4],
	"Narrow five-point preview charts should show first, middle, and last x labels"
);

assert.deepStrictEqual(
	previewLabelIndexes(5, 170, { maxVisible: 2 }),
	[0, 4],
	"Narrow five-point preview charts should only show edge value labels"
);

assert.deepStrictEqual(
	previewLabelIndexes(8, 170, { maxVisible: 3 }),
	[0, 4, 7],
	"Narrow dense preview charts should sample labels instead of rendering every tick"
);

assert.deepStrictEqual(
	previewLabelIndexes(4, 320, { maxVisible: 6 }),
	[0, 1, 2, 3],
	"Wider preview charts should keep all short labels when space permits"
);

assert.strictEqual(shouldShowPreviewLabel(2, 5, 170, { maxVisible: 3 }), true);
assert.strictEqual(shouldShowPreviewLabel(1, 5, 170, { maxVisible: 3 }), false);

assert(
	!simpleChartSource.includes('selectAll(".bar-label")') &&
		!simpleChartSource.includes('attr("class", "line-x-label")'),
	"SimpleChart previews should omit horizontal-axis labels in the three-column table"
);

assert(
	!simpleChartSource.includes('attr("class", "y-axis-tick")') &&
		!simpleChartSource.includes('attr("class", "y-axis-grid")'),
	"SimpleChart previews should omit vertical-axis labels and gridlines in the three-column table"
);

assert(
	simpleChartSource.includes('selectAll(".bar-value-label")') &&
		simpleChartSource.includes("compactSvgText(d.display, 10)"),
	"SimpleChart bar previews should show compact value labels instead of category-axis labels"
);

assert(
	simpleChartSource.includes("const previewHorizontalGap =") &&
		!simpleChartSource.includes("(width - margin.left - margin.right) / barCount - 10") &&
		!simpleChartSource.includes("barWidth + 10"),
	"Bar previews should use adaptive gaps so one- and two-bar charts fill more of the available width"
);

assert(
	simpleChartSource.includes("const previewSingleBarFill = 0.42") &&
		simpleChartSource.includes("const previewSingleBarMaxWidth = 54") &&
		!simpleChartSource.includes("const previewSingleBarFill = 0.72"),
	"Single-value bar previews should stay narrow enough to match the paper-like compact bar style"
);

assert(
	simpleChartSource.includes("const previewLinePadding =") &&
		!simpleChartSource.includes(".padding(0.45)"),
	"Line previews should use compact endpoint padding instead of leaving large side gutters"
);

assert(
	simpleChartSource.includes("const previewStackSideGutter =") &&
		simpleChartSource.includes("const previewStackMaxBarWidth = 52") &&
		simpleChartSource.includes("Math.min(58, Math.max(34, width * 0.28))") &&
		!simpleChartSource.includes("Math.min(38, Math.max(16, availableBarWidth * 0.72))"),
	"Stacked previews should reserve wider legend gutters and keep the stacked bar compact enough for labels"
);

console.log("simpleChartAxisDensity tests passed");
