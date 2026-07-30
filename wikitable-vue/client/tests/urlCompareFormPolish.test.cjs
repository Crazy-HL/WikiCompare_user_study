const assert = require("assert");
const fs = require("fs");
const path = require("path");

const componentPath = path.join(__dirname, "..", "src", "components", "UrlCompareForm.vue");
const source = fs.readFileSync(componentPath, "utf8");
const sessionStoreSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "sessionStore.js"),
	"utf8"
);

assert(
	source.includes('class="summary-status"'),
	"UrlCompareForm should keep the compared article summary as a distinct strip status"
);
assert(
	source.includes('{{ isExpanded ? "Collapse" : "Change" }}'),
	"UrlCompareForm should use concise collapsed/expanded toggle labels"
);
assert(
	!source.includes("Change URLs") && !source.includes(">Hide<"),
	"UrlCompareForm should not regress to the old bulky toggle labels"
);
assert(
	source.includes(".url-form") && source.includes("grid-template-columns: 1fr 1fr auto"),
	"UrlCompareForm should keep the compact two-field desktop form layout"
);
assert(
	/\.url-shell\s*\{[^}]*position:\s*fixed;[^}]*top:\s*10px;[^}]*right:\s*12px;/s.test(source) &&
		/\.url-shell:not\(\.expanded\)\s*\{[^}]*width:\s*96px;[^}]*height:\s*52px;/s.test(source) &&
		/\.url-shell:not\(\.expanded\)\s+\.url-summary\s*\{[^}]*opacity:\s*0;[^}]*pointer-events:\s*none;/s.test(source) &&
		source.includes(".url-shell:not(.expanded):hover .url-summary") &&
		source.includes(".url-shell:not(.expanded):focus-within .url-summary") &&
		/\.url-shell:not\(\.expanded\)\s+\.summary-text\s*\{[^}]*position:\s*absolute;[^}]*width:\s*1px;[^}]*height:\s*1px;/s.test(source) &&
		/\.url-shell\.expanded\s*\{[^}]*left:\s*50%;[^}]*transform:\s*translateX\(-50%\);/s.test(source) &&
		/\.url-shell\.expanded\s*\{[^}]*max-height:\s*calc\(100vh - 24px\);/s.test(source),
	"UrlCompareForm should hide the floating Change control until users hover or focus the top-right hot zone"
);
assert(
	source.includes("initialUrlForSide") &&
		source.includes('const leftUrl = ref(initialUrlForSide("left"));') &&
		source.includes('const rightUrl = ref(initialUrlForSide("right"));'),
	"UrlCompareForm should initialize URL inputs from the active session or latest history before falling back to examples"
);
assert(
	source.includes("oldid=1273871505") && source.includes("oldid=1297943898"),
	"UrlCompareForm should use fixed revision URLs for the Korea/Japan example pair"
);
assert(
	source.includes("fixedExampleUrl"),
	"UrlCompareForm should upgrade stale unversioned Korea/Japan history entries to fixed revision URLs"
);
assert(
	source.includes("presetForUrls") &&
		source.includes("loadOptionsForUrls") &&
		source.includes("leftTitle: preset.left.title") &&
		source.includes("rightTitle: preset.right.title"),
	"UrlCompareForm should preserve preset article titles when users compare URLs that match a built-in material"
);
assert(
	source.includes("MATERIAL_PRESETS") &&
		source.includes('class="material-panel"') &&
		source.includes("@click=\"selectMaterial(preset)\"") &&
		source.includes("leftTitle: preset.left.title") &&
		source.includes("rightTitle: preset.right.title"),
	"UrlCompareForm should expose built-in material groups and pass preset titles through to the session request"
);
assert(
	source.includes('class="history-delete"') &&
		source.includes('@click.stop="deleteHistory(item.key)"') &&
		source.includes("store.removeHistory(itemKey)"),
	"UrlCompareForm should let users delete unwanted recent comparison groups without selecting them"
);
assert(
		source.includes("<textarea") &&
		source.includes("Article URL or pasted article text") &&
		source.includes("buildLoadRequest") &&
		source.includes("inputContent") &&
		sessionStoreSource.includes("buildSessionPayload") &&
		sessionStoreSource.includes("leftContent") &&
		sessionStoreSource.includes("rightContent"),
	"UrlCompareForm should let pasted article text travel as explicit manual content instead of being treated as a URL"
);

console.log("urlCompareFormPolish tests passed");
