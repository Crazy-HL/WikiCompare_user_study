const assert = require("assert");
const fs = require("fs");
const path = require("path");

const parentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "ParentComponent.vue"),
	"utf8"
);

assert(
	parentSource.includes("sourceNodeIndex") &&
		parentSource.includes("buildSourceNodeIndex"),
	"ParentComponent should build a reusable data-source-id node index for article panes"
);

assert(
	parentSource.includes("appliedHighlightNodes") &&
		parentSource.includes("clearAppliedHighlightNodes"),
	"ParentComponent should remember previously highlighted nodes and clear only that small set"
);

assert(
	!parentSource.includes('root.querySelectorAll(".source-highlight, .source-related-highlight, .source-pinned, .source-related-pinned")'),
	"ParentComponent should not scan the entire article pane just to clear highlight classes"
);

assert(
	parentSource.includes("nodesForSourceId(id)") &&
		!parentSource.includes('root.querySelectorAll(`[data-source-id="${cssEscape(id)}"]`)'),
	"ParentComponent should apply highlights through the cached source-id index instead of repeated selector scans"
);

assert(
	parentSource.includes("scrollArticlePaneToNode") &&
		!parentSource.includes("scrollIntoView"),
	"ParentComponent should scroll its own article pane directly instead of using expensive scrollIntoView"
);

assert(
	parentSource.includes('flush: "sync"'),
	"ParentComponent should run reveal scrolling synchronously when the click request is emitted"
);

assert(
	!parentSource.includes("() => nextTick(applyHighlights)"),
	"ParentComponent should apply hover/click highlight class changes without waiting for another Vue tick"
);

console.log("parentComponentHighlightPerformance tests passed");
