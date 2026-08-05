const assert = require("assert");
const fs = require("fs");
const path = require("path");

const {
	PAPER_PIE_COLORS,
	FALLBACK_CATEGORY_COLORS,
	buildCategoryColorMap,
	colorFromMap,
} = require("../src/js/chartTheme");

const pieMap = buildCategoryColorMap(
	["China", "United States", "Others", "United States", "China"],
	PAPER_PIE_COLORS
);
assert.strictEqual(
	colorFromMap(pieMap, "China"),
	colorFromMap(pieMap, "china"),
	"The same pie element should resolve to the same color across left/right charts"
);
assert.strictEqual(
	colorFromMap(pieMap, "United States"),
	PAPER_PIE_COLORS[1],
	"Duplicate pie labels should keep the first shared assignment instead of shifting by local side index"
);
assert.notStrictEqual(
	colorFromMap(pieMap, "China"),
	colorFromMap(pieMap, "United States"),
	"Different pie elements should receive different colors"
);

const stackedMap = buildCategoryColorMap(
	["Machinery", "Vehicles", "Machinery", "Chemicals"],
	FALLBACK_CATEGORY_COLORS
);
assert.strictEqual(
	colorFromMap(stackedMap, "machinery"),
	FALLBACK_CATEGORY_COLORS[0],
	"Stacked charts should also use one row-level color assignment per element"
);
assert.notStrictEqual(
	colorFromMap(stackedMap, "Machinery"),
	colorFromMap(stackedMap, "Vehicles"),
	"Different stacked-chart elements should not share a color within the row palette"
);

const componentDir = path.join(__dirname, "..", "src", "components", "compoents_base");
const compareTableSource = fs.readFileSync(path.join(componentDir, "CompareTable.vue"), "utf8");
const simpleChartSource = fs.readFileSync(path.join(componentDir, "SimpleChart.vue"), "utf8");
const fullChartSource = fs.readFileSync(path.join(componentDir, "FullChart.vue"), "utf8");

assert(
	compareTableSource.includes(':categoryColors="rowCategoryColorMap(row)"') &&
		compareTableSource.includes(':categoryColors="currentChart.categoryColors"') &&
		compareTableSource.includes('categoryColors: rowCategoryColorMap(row)'),
	"CompareTable should pass the same row-level category color map to left/right previews and the expanded chart"
);
assert(
	compareTableSource.includes('const rowCategoryColorMap = row =>') &&
		compareTableSource.includes('["left", "right"].forEach(side =>') &&
		compareTableSource.includes('buildCategoryColorMap(labels, palette)'),
	"CompareTable should build category colors from both sides of the row, not from each side independently"
);
assert(
	simpleChartSource.includes('colorFromMap(props.categoryColors, name) || paperPieColors[index % paperPieColors.length]') &&
		simpleChartSource.includes('color: pieColorFor(d.name, i)'),
	"Thumbnail pie charts should use the shared row color for matching labels before falling back to local paper-palette order"
);
assert(
	fullChartSource.includes('categoryColors: {') &&
		fullChartSource.includes('pieLegendLabelForPoint(item, index') &&
		fullChartSource.includes('colorFromMap(props.categoryColors, name) || PIE_COLORS[index % PIE_COLORS.length]') &&
		fullChartSource.includes('categoryColor(item.label, index, props.categoryColors)'),
	"Expanded pie and stacked charts should use the same shared row category colors as the previews"
);

console.log("sharedCategoryColors tests passed");
