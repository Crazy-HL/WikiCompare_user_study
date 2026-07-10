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
const fullChartSource = fs.readFileSync(
	path.join(componentDir, "FullChart.vue"),
	"utf8"
);
const mergedChartSource = fs.readFileSync(
	path.join(componentDir, "MergedComparisonChart.vue"),
	"utf8"
);

[
	["SimpleChart", simpleChartSource],
	["FullChart", fullChartSource],
	["MergedComparisonChart", mergedChartSource],
].forEach(([name, source]) => {
	assert(
		source.includes("@/js/chartTheme"),
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
	fullChartSource.includes("lineStyle: { width: CHART_LINE_WIDTH }"),
	"Expanded line charts should use the same line weight token as thumbnails"
);
assert(
	mergedChartSource.includes("lineStyle: { width: CHART_LINE_WIDTH }"),
	"Merged line charts should use the same line weight token as thumbnails"
);

console.log("chartThemeConsistency tests passed");
