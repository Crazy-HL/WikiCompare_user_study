const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const tableSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);
const storeSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "sessionStore.js"),
	"utf8"
);
const parentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "ParentComponent.vue"),
	"utf8"
);

assert(
	tableSource.includes('@click="togglePinnedHighlight(row, $event)"'),
	"Middle attribute cells should toggle a pinned evidence highlight when clicked"
);
assert(
	tableSource.includes("pinnedMetaCell") &&
		tableSource.includes("setPinnedMetaCell") &&
		!tableSource.includes(":class=\"{ 'is-pinned': isPinnedRow(row) }\"") &&
		!tableSource.includes("const isPinnedRow"),
	"Middle attribute cells should toggle their pinned class locally without rerendering the comparison table"
);
assert(
	tableSource.includes('class="meta-click-zone"'),
	"Middle attribute content should separate the clickable lock area from action buttons"
);
assert(
	tableSource.includes('@click.stop="emit(\'compareAttribute\', row)"') &&
		tableSource.includes('@click.stop="showCombinedChart(row)"'),
	"Middle action buttons should not toggle the pinned highlight"
);
assert(
	storeSource.includes("pinnedRelatedSourceIds") &&
		storeSource.includes("pinnedHighlightKey") &&
		storeSource.includes("togglePinnedHighlight"),
	"sessionStore should track and toggle pinned primary and related evidence IDs"
);
assert(
	tableSource.includes("store.highlight(") && !tableSource.includes("highlightAndReveal("),
	"Hovering table rows should highlight evidence without triggering article scrolling"
);
assert(
	storeSource.includes("pinnedRevealSourceIds") &&
		storeSource.includes("isInfoboxSourceId"),
	"sessionStore should compute click-lock reveal order with infobox-aware helpers"
);
assert(
	storeSource.includes("revealBehavior") &&
		storeSource.includes('this.revealBehavior = "auto"'),
	"Middle-cell click-lock should request an immediate reveal instead of animated smooth scrolling"
);
assert(
	parentSource.includes("scrollArticlePaneToNode") &&
		parentSource.includes('store.revealBehavior === "smooth"'),
	"ParentComponent should honor the reveal behavior requested by the interaction source"
);
assert(
	parentSource.includes("() => revealHighlightedSource()"),
	"ParentComponent should reveal clicked evidence immediately without waiting for the next Vue tick"
);

const loadSessionStoreForTest = () => {
	const transformedSource = storeSource
		.replace('import { reactive } from "vue";', "const reactive = value => value;")
		.replace('import { postJson } from "@/api";', "const postJson = async () => ({});")
		.replace(/export const /g, "const ");
	const sandbox = {
		module: { exports: {} },
		require: dependency => {
			if (dependency === "@/js/sessionHistory") {
				return {
					addSessionToHistory: history => history,
					findHistoryByKey: () => null,
					findHistoryByUrls: () => null,
					loadHistory: () => [],
					removeHistoryByKey: history => history,
					saveHistory: () => {},
					sessionPairKey: () => ""
				};
			}
			if (dependency === "@/js/offlineSupport") {
				return {
					isOfflineNow: () => false,
					WIKICOMPARE_OFFLINE_MESSAGE: "offline",
				};
			}
			throw new Error(`Unexpected dependency in test: ${dependency}`);
		}
	};
	vm.runInNewContext(
		`${transformedSource}\nmodule.exports = { pinnedRevealSourceIds, sessionStore };`,
		sandbox
	);
	return sandbox.module.exports;
};

const { pinnedRevealSourceIds, sessionStore } = loadSessionStoreForTest();
const localArray = values => Array.from(values);

assert.deepStrictEqual(
	localArray(pinnedRevealSourceIds(
		["left-info-8", "right-info-8"],
		["left-s-17-1", "right-s-1-2"]
	)),
	["left-info-8", "right-info-8", "left-s-17-1", "right-s-1-2"],
	"Click-lock should reveal primary infobox evidence before related body evidence"
);

assert.deepStrictEqual(
	localArray(pinnedRevealSourceIds(
		["left-s-1-1"],
		["left-s-1-2"]
	)),
	["left-s-1-2", "left-s-1-1"],
	"Click-lock should fall back to related body evidence when no infobox evidence exists"
);

sessionStore.togglePinnedHighlight(
	"financial-row",
	["left-info-8", "right-info-8"],
	["left-s-17-1", "right-s-1-2"]
);
assert.deepStrictEqual(
	localArray(sessionStore.revealSourceIds),
	["left-info-8", "right-info-8", "left-s-17-1", "right-s-1-2"],
	"Middle-cell clicks should pass infobox-first reveal IDs to article panes"
);
assert.strictEqual(
	sessionStore.revealBehavior,
	"auto",
	"Middle-cell clicks should use immediate article pane reveal behavior"
);

console.log("compareTablePinnedHighlight tests passed");
