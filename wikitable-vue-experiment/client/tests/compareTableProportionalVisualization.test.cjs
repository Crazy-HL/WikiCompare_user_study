const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);

assert(
	source.includes('if (chartType === "pie") return "pie-chart"') &&
		source.includes('if (chartType === "stacked") return "stacked-chart"'),
	"CompareTable should honor backend-selected proportional pie/stacked chart types after backend normalizes part-whole data"
);

console.log("compareTable proportional visualization tests passed");
