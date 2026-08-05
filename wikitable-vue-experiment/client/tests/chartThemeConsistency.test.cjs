const assert = require("assert");
const fs = require("fs");
const path = require("path");

const componentDir = path.join(
	__dirname,
	"..",
	"src",
	"components",
	"compoents_base"
);

const simpleChartSource = fs.readFileSync(
	path.join(componentDir, "SimpleChart.vue"),
	"utf8"
);
const fullChartComponentSource = fs.readFileSync(
	path.join(componentDir, "FullChart.vue"),
	"utf8"
);
const fullChartOptionSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "fullChartAdaptiveOptions.js"),
	"utf8"
);
const fullChartSource = `${fullChartComponentSource}
${fullChartOptionSource}`;
const mergedChartComponentSource = fs.readFileSync(
	path.join(componentDir, "MergedComparisonChart.vue"),
	"utf8"
);
const mergedChartOptionSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "mergedComparisonAdaptiveOptions.js"),
	"utf8"
);
const mergedChartSource = `${mergedChartComponentSource}
${mergedChartOptionSource}`;

[
	["SimpleChart", simpleChartSource],
	["FullChart", fullChartSource],
	["MergedComparisonChart", mergedChartSource],
].forEach(([name, source]) => {
	assert(
		source.includes("@/js/chartTheme") || source.includes('require("./chartTheme")'),
		`${name} should use the shared chart theme so thumbnails, expanded charts, and merged charts stay visually consistent`
	);
});

[
	["FullChart", fullChartSource],
	["MergedComparisonChart", mergedChartSource],
].forEach(([name, source]) => {
	assert(
		!source.includes("#3867a8") && !source.includes("#c94f45"),
		`${name} should not keep the previous expanded-chart palette`
	);
	assert(
		!source.includes("stackedPalette"),
		`${name} should not define a separate stacked palette`
	);
});


assert(
	fullChartComponentSource.includes("PAPER_PIE_COLORS") &&
		fullChartComponentSource.includes("const PIE_COLORS = PAPER_PIE_COLORS"),
	"Expanded pie charts should import and use the same paper-aligned palette as pie previews"
);

const pieOptionStart = fullChartComponentSource.indexOf("const pieOption = () => {");
const pieOptionEnd = fullChartComponentSource.indexOf("const stackedOption = () => {", pieOptionStart);
assert(
	pieOptionStart >= 0 && pieOptionEnd > pieOptionStart,
	"FullChart should define pieOption before stackedOption"
);
const pieOptionSource = fullChartComponentSource.slice(pieOptionStart, pieOptionEnd);
assert(
	pieOptionSource.includes("itemStyle: pieSliceStyle(PIE_COLORS[0])") &&
		pieOptionSource.includes("itemStyle: pieSliceStyle(PIE_COLORS[index % PIE_COLORS.length])") &&
		!pieOptionSource.includes("itemStyle: { color: COLORS[0] }") &&
		!pieOptionSource.includes("itemStyle: { color: COLORS[index % COLORS.length] }"),
	"Expanded pie series colors should match thumbnail pie colors instead of the generic chart palette"
);

const simplePieStart = simpleChartSource.indexOf("const renderPieChart = () => {");
const simplePieEnd = simpleChartSource.indexOf("const renderBarChart = () => {", simplePieStart);
assert(
	simplePieStart >= 0 && simplePieEnd > simplePieStart,
	"SimpleChart should define renderPieChart before renderBarChart"
);
const simplePieSource = simpleChartSource.slice(simplePieStart, simplePieEnd);
assert(
	simplePieSource.includes("color: paperPieColors[i % paperPieColors.length]") &&
		!simplePieSource.includes("d.color || paperPieColors"),
	"Thumbnail pie slices should use the same fixed paper palette that expanded pie slices use"
);
assert(
	pieOptionSource.includes('icon: "circle"') &&
		fullChartComponentSource.includes('borderColor: "#ffffff"') &&
		fullChartComponentSource.includes("opacity = 0.92"),
	"Expanded pie charts should keep the same circular legend and white-separated slice style as thumbnail pies"
);

assert(
	pieOptionSource.includes("return isSingle") &&
		pieOptionSource.includes('params.data?.shortDisplay || params.data?.display || "-"') &&
		!pieOptionSource.includes("`${params.name}\n${params.data?.shortDisplay || params.value}`"),
	"Expanded pie slice labels should show the numeric value only because the legend already explains colors"
);

assert(
	fullChartSource.includes("lineStyle: { width: CHART_LINE_WIDTH }"),
	"Expanded line charts should use the same line weight token as thumbnails"
);
assert(
	mergedChartSource.includes("lineStyle: { width: CHART_LINE_WIDTH }"),
	"Merged line charts should use the same line weight token as thumbnails"
);

console.log("chartThemeConsistency tests passed");
