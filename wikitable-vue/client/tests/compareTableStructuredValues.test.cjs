const assert = require("assert");
const fs = require("fs");
const path = require("path");

const componentPath = path.join(
	__dirname,
	"..",
	"src",
	"components",
	"compoents_base",
	"CompareTable.vue"
);
const source = fs.readFileSync(componentPath, "utf8");

assert(
	source.includes('require("@/js/comparisonDisplayPlan")'),
	"CompareTable should import the shared comparison display plan"
);
assert(
	source.includes("displayItems(row, 'left')") &&
		source.includes("displayItems(row, 'right')"),
	"CompareTable should render shared display-plan items for both article sides"
);
assert(
	source.includes("shouldShowDisplayLines(row)") &&
		source.includes('chartVisualization(row) === "text-only"'),
	"CompareTable should reserve flat display lines for text-like rows, not chartable stacked/bar/line rows"
);
assert(
	source.includes("comparison-value-line") &&
		source.includes("comparison-value-label") &&
		source.includes("comparison-value-text"),
	"CompareTable should use a flat label/value line style"
);
assert(
	!source.includes("text-pair-card") && !source.includes("structured-item"),
	"CompareTable should not keep old text-card or structured-chip table rendering"
);
assert(
	source.indexOf("isCreditRatingRow(row)") < source.indexOf("displayItems(row, 'left')"),
	"Credit rating rows should use their agency-specific display before generic display lines"
);

console.log("compareTableStructuredValues tests passed");
