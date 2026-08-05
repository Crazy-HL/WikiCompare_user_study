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
const compareTableSource = fs.readFileSync(
	path.join(componentDir, "CompareTable.vue"),
	"utf8"
);
const div2Source = fs.readFileSync(
	path.join(componentDir, "..", "Div2.vue"),
	"utf8"
);
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

assert(
	!simpleChartSource.includes('attr("class", "line-x-label")') &&
		!simpleChartSource.includes('selectAll(".bar-label")'),
	"Three-column preview charts should not render horizontal-axis labels"
);

assert(
	!simpleChartSource.includes('attr("class", "y-axis-tick")') &&
		!simpleChartSource.includes('attr("class", "y-axis-grid")'),
	"Three-column preview charts should not render vertical-axis labels or gridlines"
);

assert(
	simpleChartSource.includes('attr("class", "bar-value-label")') &&
		simpleChartSource.includes("shortValueText(item, props.type)"),
	"Bar previews should replace category-axis labels with compact value labels"
);

assert(
	!simpleChartSource.includes('attr("class", "pie-value-label")') &&
		simpleChartSource.includes('attr("class", "pie-legend-dot")') &&
		simpleChartSource.includes("pieLegendLabelForPoint") &&
		simpleChartSource.includes("formatChartNumber(d.displayValue ?? d.value, props.type)") &&
		!simpleChartSource.includes('attr("class", "pie-label-line")'),
	"Paper-style pie previews should keep values in a compact legend instead of crowded in-slice labels"
);

assert(
	compareTableSource.includes(":yDomain=\"chartDomain(row)\"") &&
		compareTableSource.includes("const chartDomain = row =>") &&
		compareTableSource.includes("lineChartDomain"),
	"Left and right preview charts should receive a shared row-level y domain"
);

assert(
	compareTableSource.includes("meta-compact-line") &&
		!compareTableSource.includes('class="score-track"') &&
		!compareTableSource.includes("score-pill") &&
		!compareTableSource.includes("displayScore(row)"),
	"Middle attribute cells should show only compact metadata, not visible percentage score labels"
);

assert(
	compareTableSource.includes("justify-content: center;") &&
		compareTableSource.includes(".meta-cell") &&
		compareTableSource.includes(".value-cell"),
	"Three-column table cells should vertically center chart and attribute content within each row"
);

assert(
	compareTableSource.includes("canMergeChart(row)") &&
		compareTableSource.includes(':disabled="!canMergeChart(row)"'),
	"Merge chart action should be disabled for rows without comparable numeric chart data"
);

assert(
	/grid-template-columns:\s*minmax\(150px,\s*1fr\)\s*minmax\(82px,\s*96px\)\s*minmax\(150px,\s*1fr\)/s.test(compareTableSource) &&
		/min-height:\s*96px;/.test(compareTableSource) &&
		/min-height:\s*84px;/.test(compareTableSource) &&
		/height:\s*100%;/.test(compareTableSource) &&
		/min-height:\s*100%;/.test(compareTableSource) &&
		/\.vis-container\s*\{[^}]*flex:\s*0 0 clamp\(330px,\s*56vh,\s*400px\);[^}]*height:\s*clamp\(330px,\s*56vh,\s*400px\);[^}]*min-height:\s*330px;/s.test(div2Source),
	"Three-column table should keep the overall viewport height while giving each preview row enough vertical chart space"
);

assert(
	mergedChartSource.includes("emptyMergedChart") &&
		mergedChartSource.includes("dataZoom: []") &&
		mergedChartSource.includes("hideOverlap: true") &&
		mergedChartSource.includes("shouldShowPointLabels"),
	"Merged charts should handle empty data and avoid cluttered axis/zoom/point-label rendering"
);

console.log("paperAlignedComparisonTable tests passed");
