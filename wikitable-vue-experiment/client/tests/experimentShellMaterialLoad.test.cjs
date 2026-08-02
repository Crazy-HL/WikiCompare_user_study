const assert = require("assert");
const fs = require("fs");
const path = require("path");

const shellPath = path.join(__dirname, "../src/components/experiment/ExperimentShell.vue");
const source = fs.readFileSync(shellPath, "utf8");

const loaderMatch = source.match(/const loadCurrentMaterialSession = async stage => \{([\s\S]*?)\n\t\};/);
assert(loaderMatch, "ExperimentShell should define loadCurrentMaterialSession");
const loaderSource = loaderMatch[1];

assert(
	loaderSource.includes("await sessionStore.loadSession"),
	"material loader should await sessionStore.loadSession"
);
assert(
	/sessionStore\.error[\s\S]*throw new Error/.test(loaderSource),
	"material loader should throw when sessionStore reports a load error so stale cached material cannot become a ready stage"
);

console.log("experiment shell material load tests passed");
