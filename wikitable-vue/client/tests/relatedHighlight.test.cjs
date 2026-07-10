const assert = require("assert");
const fs = require("fs");
const path = require("path");

const storeSource = fs.readFileSync(path.join(__dirname, "..", "src", "js", "sessionStore.js"), "utf8");
const tableSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);
const parentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "ParentComponent.vue"),
	"utf8"
);

assert(
	storeSource.includes("relatedHighlightedSourceIds"),
	"sessionStore should track related source highlights separately"
);
assert(
	tableSource.includes("leftRelatedSourceIds") && tableSource.includes("rightRelatedSourceIds"),
	"CompareTable should pass row related source IDs during hover"
);
assert(
	parentSource.includes("source-related-highlight"),
	"ParentComponent should render a softer related evidence highlight"
);
assert(
	parentSource.includes("store.relatedHighlightedSourceIds"),
	"ParentComponent should watch related source IDs"
);
assert(
	parentSource.includes("source-related-pinned") &&
		parentSource.includes("rgba(255, 228, 117, 0.42)") &&
		parentSource.includes("outline: 2px solid rgba(217, 144, 47, 0.42)"),
	"ParentComponent should render locked related text evidence with a clearly visible highlight"
);

console.log("relatedHighlight tests passed");
