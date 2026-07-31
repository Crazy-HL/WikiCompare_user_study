const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);

assert(
	source.includes("scoreTitle(row)"),
	"CompareTable should keep score details available as metadata without rendering a visible middle-column percent label"
);
assert(
	source.includes("row.rankScore ?? row.score"),
	"CompareTable should prefer weighted rankScore over raw score in the metadata title"
);
assert(
	!source.includes("displayScore(row)") &&
		!source.includes("score-pill") &&
	!source.includes(":title=\"`差异度 ${formatScore(row.score)}`\"") &&
		!source.includes("{{ formatScore(row.score) }}") &&
		!source.includes("width: formatScore(row.score)"),
	"CompareTable should not render a visible percentage score in the middle attribute column"
);

console.log("compareTableRankScore tests passed");
