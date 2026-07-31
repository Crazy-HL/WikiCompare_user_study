const assert = require("assert");
const fs = require("fs");
const path = require("path");

const fullChartPath = path.join(
	__dirname,
	"..",
	"src",
	"components",
	"compoents_base",
	"FullChart.vue"
);
const compareTablePath = path.join(
	__dirname,
	"..",
	"src",
	"components",
	"compoents_base",
	"CompareTable.vue"
);

const fullChartComponentSource = fs.readFileSync(fullChartPath, "utf8");
const fullChartOptionSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "fullChartAdaptiveOptions.js"),
	"utf8"
);
const fullChartSource = `${fullChartComponentSource}
${fullChartOptionSource}`;
const compareTableSource = fs.readFileSync(compareTablePath, "utf8");

assert(
	fullChartSource.includes("categoryLabelForPoint"),
	"FullChart should use a local category label helper for bar-like charts"
);
assert(
	fullChartSource.includes("rendered.map((item, index) => categoryLabelForPoint(item, index, {") &&
			fullChartSource.includes("fallback: fieldKey") &&
			fullChartSource.includes("total: rendered.length"),
	"FullChart bar charts should prefer comparison labels over years on the x-axis"
);
assert(
	fullChartSource.includes("dataPoints.map((item, index) => xLabelForPoint(item, index))"),
	"FullChart line charts should still use year-like x labels"
);
assert(
	fullChartSource.includes("shortValueText") &&
			fullChartSource.includes("function fullChartShortDisplay") &&
			fullChartSource.includes("axisType"),
	"FullChart value labels should use the shared value formatter so stale display text cannot turn years into values"
);

assert(
	!fullChartSource.includes("display.lastIndexOf(\":\")"),
	"FullChart should not hand-slice display text after a colon for value labels"
);
assert(
	!compareTableSource.includes('class="chart-details"'),
	"Single-chart modal should not render duplicated raw/standardized detail cards"
);

console.log("fullChartPolish tests passed");
