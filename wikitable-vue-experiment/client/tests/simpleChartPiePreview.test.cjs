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
	source.includes("const legendData = processedData.filter(d => !d.isRemainder)") &&
		!source.includes("pieData.value.slice(0, 4)"),
	"Pie legends should show all categories instead of truncating after four items"
);
assert(
	source.includes("const hasCornerPieLegend = pieData.value.length > 1") &&
		source.includes("const topLegendReservedHeight = hasCornerPieLegend") &&
		source.includes("containerWidth * (hasCornerPieLegend ? 0.38 : 0.42)") &&
		source.includes("hasCornerPieLegend ? 58 : 62"),
	"Pie previews should keep the pie large by using upper-corner legend space instead of squeezing side columns"
);
assert(
	source.includes('attr("class", "pie-value-label")') &&
		source.includes("formatChartNumber(d.data.displayValue ?? d.data.value, props.type)"),
	"Pie previews should place readable values directly on sufficiently large slices"
);

assert(
	source.includes("PAPER_PIE_COLORS") &&
		source.includes("paperPieColors") &&
		source.includes("colorFromMap(props.categoryColors, name) || paperPieColors[index % paperPieColors.length]") &&
		source.includes("color: pieColorFor(d.name, i)") &&
		!source.includes("d.color || paperPieColors[i % paperPieColors.length]"),
	"Pie previews should use shared row colors before falling back to the paper-aligned muted palette"
);
assert(
	source.includes('attr("class", "pie-legend-dot")') &&
		source.includes('.append("circle")') &&
		!source.includes('.append("rect")\n\t\t\t\t\t\t\t.attr("width", legendItemSize)'),
	"Pie legends should use lightweight circular swatches matching the paper preview style"
);
assert(
	!source.includes("const valueText = formatChartNumber(d.displayValue ?? d.value, props.type)") &&
		!source.includes("`${label} ${valueText}`") &&
		source.includes('text(d => compactMiddleText(d.name || "", maxLegendChars))'),
	"Pie legends should only explain what each color means, not repeat numeric values"
);

assert(
	source.includes('text(d => compactMiddleText(d.name || "", maxLegendChars))') &&
		!source.slice(source.indexOf('cornerPieLegendGroups'), source.indexOf('const renderBarChart')).includes("pieLegendLabelForPoint("),
	"Pie preview legends should use the already-cleaned slice name instead of re-inferring labels from rendered data"
);

console.log("simpleChartPiePreview tests passed");
