const rawErrorText = error => (
	error?.response?.data?.error ||
	error?.message ||
	"加载阶段材料或问题时出错。"
);

const participantStageLoadErrorMessage = error => {
	const message = String(rawErrorText(error));
	if (/^Questions for .+ are not frozen$/.test(message)) {
		return "当前材料的问题尚未冻结，请联系研究人员。";
	}
	if (/^Static table for .+ is not frozen$/.test(message) || /^Static table for .+ is incomplete$/.test(message)) {
		return "当前 ChatGPT 阅读表格尚未冻结，请联系研究人员。";
	}
	if (/Network Error/i.test(message)) {
		return "无法连接实验服务器，请联系研究人员。";
	}
	return message;
};

module.exports = {
	participantStageLoadErrorMessage,
};
