const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);

assert(
	/\.middle-column\s*\{[^}]*align-items:\s*center;/s.test(source),
	"Middle comparison cells should center their column content"
);
assert(
	/\.icon-actions\s*\{[^}]*width:\s*100%;[^}]*justify-content:\s*center;/s.test(source),
	"Comparison action buttons should use the full middle cell width and center within it"
);

console.log("compareTableButtonAlignment tests passed");
