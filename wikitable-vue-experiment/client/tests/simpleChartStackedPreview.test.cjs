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
assert(
	source.includes("const previewStackMaxBarWidth = 52") &&
		source.includes("Math.min(58, Math.max(34, width * 0.28))"),
	"Stacked previews should shrink the bar and reserve wider side gutters so legends can show more complete labels"
);

console.log("simpleChartStackedPreview tests passed");
