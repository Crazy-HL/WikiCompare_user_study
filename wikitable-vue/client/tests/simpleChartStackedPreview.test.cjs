const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "SimpleChart.vue"),
	"utf8"
);

assert(
	!source.includes("showCompactStackPreview"),
	"SimpleChart should render stacked-chart rows as charts, not compact text lists"
);
assert(
	source.includes('visualization === "stacked-chart"') &&
		source.includes('ref="stackedContainer"'),
	"SimpleChart should keep the stacked chart rendering branch"
);

console.log("simpleChartStackedPreview tests passed");
