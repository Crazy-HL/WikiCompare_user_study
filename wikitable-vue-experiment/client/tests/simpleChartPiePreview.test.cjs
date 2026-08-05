const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "SimpleChart.vue"),
	"utf8"
);

assert(
	source.includes('class="d3-chart-container pie-chart-container"'),
	"Pie previews should use a dedicated taller container instead of the compact default chart height"
);
assert(
	source.includes("const maxPieLegendItems = pieData.value.length") &&
		!source.includes("pieData.value.slice(0, 4)"),
	"Pie legends should show all categories instead of truncating after four items"
);
assert(
	source.includes("containerHeight * 0.38") &&
		source.includes("containerWidth * 0.42") &&
		source.includes("62"),
	"Pie previews should allocate a larger radius for dense proportional rows"
);
assert(
	source.includes("shouldShowPieSliceLabel"),
	"Dense pie previews should avoid labeling every tiny slice inside the pie"
);

console.log("simpleChartPiePreview tests passed");
