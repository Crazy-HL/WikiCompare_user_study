const assert = require("assert");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const files = [
	"src/components/Div2.vue",
	"src/components/compoents_base/CompareTable.vue",
	"src/components/compoents_base/ParentComponent.vue",
];

for (const file of files) {
	const source = fs.readFileSync(path.join(repoRoot, file), "utf8");
	assert(
		!/Wikipedia (URL|URLs|文章 URL)/.test(source),
		`${file} should describe generic source URLs instead of Wikipedia-only input`
	);
}

const parentComponent = fs.readFileSync(
	path.join(repoRoot, "src/components/compoents_base/ParentComponent.vue"),
	"utf8"
);
assert(
	parentComponent.includes(':sourceKind="article.sourceKind"'),
	"ParentComponent should pass article.sourceKind into the content renderer"
);
assert(
	parentComponent.includes("article-title") && parentComponent.includes("@media (max-width: 1180px)"),
	"ParentComponent should keep article titles readable in narrower three-column windows"
);

const wikipediaContent = fs.readFileSync(
	path.join(repoRoot, "src/components/compoents_base/WikipediaContent.vue"),
	"utf8"
);
assert(
	wikipediaContent.includes("source-web") && wikipediaContent.includes("source-wikipedia"),
	"WikipediaContent should branch styling for public web pages and Wikipedia pages"
);
assert(
	wikipediaContent.includes("@media (max-width: 1180px)") && wikipediaContent.includes("@media (max-width: 760px)"),
	"WikipediaContent should tune content density for medium and narrow windows"
);

const general = fs.readFileSync(path.join(repoRoot, "src/components/general.vue"), "utf8");
assert(
	general.includes("display: grid") &&
		general.includes("grid-template-columns: minmax(270px, 0.9fr) minmax(480px, 1.2fr) minmax(270px, 0.9fr)") &&
		general.includes("@media (max-width: 900px)") &&
		general.includes("grid-template-columns: 1fr"),
	"general layout should keep readable weighted desktop columns and a narrow-window stacked mode"
);

console.log("source copy tests passed");
