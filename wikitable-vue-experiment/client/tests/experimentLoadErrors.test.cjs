const assert = require("assert");
const { participantStageLoadErrorMessage } = require("../src/experiment/loadErrors.js");

assert.strictEqual(
	participantStageLoadErrorMessage({ response: { data: { error: "Questions for M1 are not frozen" } } }),
	"当前材料的问题尚未冻结，请联系研究人员。"
);

assert.strictEqual(
	participantStageLoadErrorMessage({ response: { data: { error: "Static table for M2 is not frozen" } } }),
	"当前 ChatGPT 阅读表格尚未冻结，请联系研究人员。"
);

assert.strictEqual(
	participantStageLoadErrorMessage({ message: "Network Error" }),
	"无法连接实验服务器，请联系研究人员。"
);

assert.strictEqual(
	participantStageLoadErrorMessage({ message: "custom failure" }),
	"custom failure"
);

console.log("experiment load error message tests passed");
