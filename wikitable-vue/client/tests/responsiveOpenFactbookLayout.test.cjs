const assert = require("assert");
const fs = require("fs");
const path = require("path");

const generalSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "general.vue"),
	"utf8"
);
const div2Source = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "Div2.vue"),
	"utf8"
);
const wikipediaContentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "WikipediaContent.vue"),
	"utf8"
);
const parentComponentSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "ParentComponent.vue"),
	"utf8"
);
const articleOutlineSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "ArticleOutline.vue"),
	"utf8"
);
const compareTableSource = fs.readFileSync(
	path.join(__dirname, "..", "src", "components", "compoents_base", "CompareTable.vue"),
	"utf8"
);

assert(
	/#root\s*\{[^}]*display:\s*grid;[^}]*grid-template-columns:\s*minmax\(270px,\s*0\.9fr\)\s*minmax\(480px,\s*1\.2fr\)\s*minmax\(270px,\s*0\.9fr\)/s.test(generalSource),
	"General layout should keep a slightly narrower center workspace while giving both article panes a little more width"
);
assert(
	!generalSource.includes("min-width: 1080px;"),
	"General layout should not force a fixed 1080px minimum that breaks narrower app windows"
);
assert(
	/\.chat-container\s*\{[^}]*flex:\s*1 1 clamp\(140px,\s*22vh,\s*210px\);/s.test(div2Source),
	"Center column chat should grow into space released by the comparison table"
);
assert(
	/\.vis-container\s*\{[^}]*flex:\s*0 0 clamp\(330px,\s*56vh,\s*400px\);[^}]*height:\s*clamp\(330px,\s*56vh,\s*400px\);[^}]*min-height:\s*330px;/s.test(div2Source) &&
		/@media \(max-height:\s*700px\)[\s\S]*?\.vis-container\s*\{[^}]*flex-basis:\s*clamp\(310px,\s*51vh,\s*370px\);[^}]*height:\s*clamp\(310px,\s*51vh,\s*370px\);[^}]*min-height:\s*310px;/s.test(div2Source) &&
		/@media \(max-width:\s*900px\)[\s\S]*?\.vis-container\s*\{[^}]*flex-basis:\s*clamp\(350px,\s*56vh,\s*410px\);[^}]*height:\s*clamp\(350px,\s*56vh,\s*410px\);[^}]*min-height:\s*350px;/s.test(div2Source),
	"Center comparison table should receive about one quarter of the current chat height while leaving the chat area usable"
);
assert(
	/\.wikipedia-content\.source-web\s*:deep\(svg\)\s*\{[^}]*width:\s*1em;[^}]*height:\s*1em;/s.test(wikipediaContentSource),
	"Imported OpenFactBook SVG icons should be constrained to icon size instead of rendering as giant placeholders"
);
assert(
	!/\.wikipedia-content\.source-web\s*:deep\(img\[src\^="\/flags\/"\]\)[\s\S]*display:\s*none/s.test(wikipediaContentSource) &&
		!/\.wikipedia-content\.source-web\s*:deep\(img\[src\^="\/maps\/"\]\)[\s\S]*display:\s*none/s.test(wikipediaContentSource),
	"Imported OpenFactBook flag and map images should remain visible once backend asset URLs are resolved"
);
assert(
	wikipediaContentSource.includes("openfactbook-profile") &&
		wikipediaContentSource.includes("openfactbook-metric-grid") &&
		wikipediaContentSource.includes("openfactbook-field-card") &&
		wikipediaContentSource.includes('[class~="stat-card"]') &&
		wikipediaContentSource.includes('[class*="lg:grid-cols-5"]'),
	"Imported OpenFactBook pages should get dedicated profile, metric-card, field-card, and metric-grid styling hooks"
);
assert(
	wikipediaContentSource.includes('[class~="h-40"]') &&
		wikipediaContentSource.includes('[class~="h-20"]') &&
		wikipediaContentSource.includes('[class~="chart-bar"]') &&
		wikipediaContentSource.includes('[class*="bg-purple-500"]') &&
		wikipediaContentSource.includes('[class*="bg-emerald-500"]'),
	"Imported OpenFactBook Historical Trends should restore original bar-chart heights and color utility classes"
);
assert(
	/#div1\s+\.article-title\s*\{[^}]*padding-right:\s*42px;/s.test(parentComponentSource) &&
		/#div3\s+\.article-title\s*\{[^}]*padding-left:\s*42px;/s.test(parentComponentSource),
	"Article titles should reserve space for the outline button on each side"
);
assert(
	/\.toggle-btn\s*\{[^}]*width:\s*30px;[^}]*height:\s*30px;/s.test(articleOutlineSource),
	"Outline buttons should stay compact so they read as pane controls rather than source-page content"
);
assert(
	/grid-template-columns:\s*minmax\(150px,\s*1fr\)\s*minmax\(82px,\s*96px\)\s*minmax\(150px,\s*1fr\)/s.test(compareTableSource),
	"Comparison table should use a narrow paper-style attribute column while preserving chart width for both value columns"
);

console.log("responsiveOpenFactbookLayout tests passed");
