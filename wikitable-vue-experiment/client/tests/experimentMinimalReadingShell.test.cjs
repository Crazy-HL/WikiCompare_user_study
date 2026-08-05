const assert = require("assert");
const fs = require("fs");
const path = require("path");

const shellSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/ExperimentShell.vue"), "utf8");

assert(
	shellSource.includes('v-if="showStageStatus"'),
	"ExperimentShell should hide the stage status bar during the ready reading interface"
);
assert(
	/showStageStatus\s*=\s*computed\(\(\) =>[\s\S]*isStageReady\.value/.test(shellSource),
	"status bar visibility should depend on isStageReady so it can remain visible for loading/error states"
);
assert(
	shellSource.includes("isAnswerPanelOpen = ref(false)"),
	"answer drawer should be closed by default to avoid covering the reading systems"
);
assert(
	shellSource.includes('class="answer-drawer-toggle"') && shellSource.includes('aria-expanded'),
	"ready stages should expose an accessible answer drawer toggle"
);
assert(
	shellSource.includes('class="answer-drawer"') && shellSource.includes('{ open: isAnswerPanelOpen }'),
	"AnswerPanel should live in a slide-over drawer instead of permanently occupying reading width"
);

const answerSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/AnswerPanel.vue"), "utf8");
assert(
	answerSource.includes('min-width: 0;') && answerSource.includes('max-width: none;'),
	"AnswerPanel dimensions should be controlled by the drawer wrapper"
);

const chatSource = fs.readFileSync(path.join(__dirname, "../src/components/experiment/ChatGptCondition.vue"), "utf8");
assert(
	chatSource.includes('class="chatgpt-composer"'),
	"ChatGPT condition should use a native-like composer instead of a bulky experiment form"
);
assert(
	!chatSource.includes('class="table-heading"'),
	"ChatGPT static output should not add a sticky experiment heading above the table"
);

console.log("experiment minimal reading shell tests passed");
