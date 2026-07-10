const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "SimpleChart.vue"),
	"utf8"
);

assert(
	!source.includes("showCompactValuePreview"),
	"SimpleChart should not replace chartable rows with compact text previews; table row sides must keep the unified chart type"
);
assert(
	source.indexOf('visualization === "bar-chart"') <
		source.indexOf('visualization === "line-chart"') &&
		source.indexOf('visualization === "line-chart"') <
		source.indexOf('visualization === "stacked-chart"'),
	"SimpleChart should keep explicit chart branches for bar, line, and stacked visualizations"
);
assert(
	source.includes('ref="barContainer"') &&
		source.includes('ref="lineContainer"') &&
		source.includes('ref="stackedContainer"'),
	"SimpleChart should render real chart containers for table visualizations"
);

console.log("simpleChartVisualizationConsistency tests passed");
