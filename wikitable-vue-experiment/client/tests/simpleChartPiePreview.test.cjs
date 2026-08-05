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
	!source.includes('selectAll(".pie-value-label")'),
	"Paper-style pie previews should keep dense values out of the pie body"
);

assert(
	source.includes("PAPER_PIE_COLORS") &&
		source.includes("paperPieColors") &&
		source.includes("color: paperPieColors[i % paperPieColors.length]") &&
		!source.includes("d.color || paperPieColors[i % paperPieColors.length]"),
	"Pie previews should use the paper-aligned muted palette directly instead of category fallback colors"
);
assert(
	source.includes('selectAll(".pie-legend-dot")') &&
		source.includes('.append("circle")') &&
		!source.includes('.append("rect")\n\t\t\t\t\t\t\t.attr("width", legendItemSize)'),
	"Pie legends should use lightweight circular swatches matching the paper preview style"
);
assert(
	!source.includes("if (showInternalPieLabels)") &&
		!source.includes('class", "pie-value-label"'),
	"Dense multi-category pie previews should avoid internal labels and keep values in legend/tooltip"
);

console.log("simpleChartPiePreview tests passed");
