const assert = require("assert");
const { MATERIAL_PRESETS, materialUrl } = require("../src/js/materialPresets.js");

assert.strictEqual(MATERIAL_PRESETS.length, 2, "There should be two built-in experiment material pairs");

const ids = MATERIAL_PRESETS.map(item => item.id);
assert.deepStrictEqual(ids, [
	"economy-korea-japan",
	"openfactbook-india-indonesia",
]);

for (const preset of MATERIAL_PRESETS) {
	assert(preset.label && preset.description && preset.type, `${preset.id} should describe the material pair`);
	assert(preset.left?.title && preset.right?.title, `${preset.id} should include both article titles`);
	const leftUrl = materialUrl(preset.left);
	const rightUrl = materialUrl(preset.right);
	assert(
		/oldid=\d+/.test(leftUrl) || leftUrl.startsWith("https://"),
		`${preset.id} left article should use a fixed oldid or real web URL`
	);
	assert(
		/oldid=\d+/.test(rightUrl) || rightUrl.startsWith("https://"),
		`${preset.id} right article should use a fixed oldid or real web URL`
	);
}

const primary = MATERIAL_PRESETS[0];
assert.strictEqual(materialUrl(primary.left), "https://en.wikipedia.org/w/index.php?title=Economy_of_South_Korea&oldid=1273871505");
assert.strictEqual(materialUrl(primary.right), "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898");

const bodyExtractionDemo = MATERIAL_PRESETS[1];
assert.strictEqual(materialUrl(bodyExtractionDemo.left), "https://openfactbook.org/countries/india/");
assert.strictEqual(materialUrl(bodyExtractionDemo.right), "https://openfactbook.org/countries/indonesia/");
assert.match(bodyExtractionDemo.description, /真实|网页|正文|10\+|population|religions|OpenFactBook/i);
assert.match(bodyExtractionDemo.label, /2026/);
assert.match(bodyExtractionDemo.left.title, /India.*2026/);
assert.match(bodyExtractionDemo.right.title, /Indonesia.*2026/);

const domains = MATERIAL_PRESETS.map(item => item.domain);
assert.deepStrictEqual(domains, ["economy", "development"]);

for (const preset of MATERIAL_PRESETS) {
	assert(
		/data|capacity|infobox|正文|图表|趋势/i.test(preset.description),
		`${preset.id} should explain why the pair is data-rich enough for the comparison table`
	);
}

console.log("materialPresets tests passed");
