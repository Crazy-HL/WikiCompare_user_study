const assert = require("assert");
const { MATERIAL_PRESETS, materialUrl } = require("../src/js/materialPresets.js");

assert.strictEqual(MATERIAL_PRESETS.length, 5, "There should be five built-in experiment material pairs");

const ids = MATERIAL_PRESETS.map(item => item.id);
assert.deepStrictEqual(ids, [
	"economy-korea-japan",
	"retail-amazon-walmart",
	"health-covid-italy-spain",
	"energy-solar-china-us",
	"demographics-india-china",
]);

for (const preset of MATERIAL_PRESETS) {
	assert(preset.label && preset.description && preset.type, `${preset.id} should describe the material pair`);
	assert(preset.left?.title && preset.right?.title, `${preset.id} should include both article titles`);
	assert(/oldid=\d+/.test(materialUrl(preset.left)), `${preset.id} left article should use a fixed oldid URL`);
	assert(/oldid=\d+/.test(materialUrl(preset.right)), `${preset.id} right article should use a fixed oldid URL`);
}

const economy = MATERIAL_PRESETS[0];
assert.strictEqual(materialUrl(economy.left), "https://en.wikipedia.org/w/index.php?title=Economy_of_South_Korea&oldid=1273871505");
assert.strictEqual(materialUrl(economy.right), "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898");

const domains = MATERIAL_PRESETS.map(item => item.domain);
assert.deepStrictEqual(domains, ["economy", "retail", "health", "energy", "demographics"]);

for (const preset of MATERIAL_PRESETS.slice(1)) {
	assert(
		/data|population|capacity|revenue|employees|percentage|transport|demographic/i.test(preset.description),
		`${preset.id} should explain why the pair is data-rich enough for the comparison table`
	);
}

console.log("materialPresets tests passed");
