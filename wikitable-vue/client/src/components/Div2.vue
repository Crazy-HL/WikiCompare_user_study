<template>
	<div class="main-container">
		<div class="chat-container">
			<div class="chat-history">
				<div
					v-for="(message, index) in chatHistory"
					:key="index"
					:class="['message', message.role, { error: message.error }]">
					<div class="message-content" v-html="message.content"></div>
					<CitationChips :citations="message.citations" />
				</div>
				<div v-if="isLoading" class="loading-indicator">
					<div class="loading-spinner"></div>
					正在处理中...
				</div>
			</div>
		</div>

		<div class="vis-container">
			<CompareTable class="compare-table" @compareAttribute="handleAttributeComparison" />
		</div>

		<div class="input-area">
			<div class="input-container">
				<textarea
					v-model="userQuestion"
					rows="2"
					placeholder="请输入你想问的问题..."
					:disabled="isLoading"></textarea>
				<div class="button-container">
					<button @click="askQuestion" :disabled="isLoading">
						{{ isLoading ? "处理中..." : "发送" }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
	import { nextTick, ref, watch } from "vue";
	import CompareTable from "@/components/compoents_base/CompareTable.vue";
	import CitationChips from "@/components/compoents_base/CitationChips.vue";
	import { postJson } from "@/api";
	import { sessionStore } from "@/js/sessionStore";

	const userQuestion = ref("");
	const chatHistory = ref([]);
	const isLoading = ref(false);

	watch(
		() => sessionStore.session?.sessionId,
		sessionId => {
			if (!sessionId) return;
			chatHistory.value = [
				{
					role: "assistant",
					content: "已加载比较会话。点击中间表格中的 Compare 可以查看属性解释，也可以直接提问。",
					timestamp: new Date().toLocaleString()
				}
			];
		}
	);

	const scrollToBottom = () => {
		nextTick(() => {
			const container = document.querySelector(".chat-history");
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
		});
	};

	const formatAnalysisResult = text => {
		if (!text) return "";
		const formatted = String(text)
			.replace(/^# (.*$)/gm, "<h1>$1</h1>")
			.replace(/^## (.*$)/gm, "<h2>$1</h2>")
			.replace(/^### (.*$)/gm, "<h3>$1</h3>")
			.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
			.replace(/\*(.*?)\*/g, "<em>$1</em>")
			.replace(/`(.*?)`/g, "<code>$1</code>")
			.replace(/(?:^|\n)\d+\.\s+(.*)/g, "<li>$1</li>")
			.replace(/(?:^|\n)-\s+(.*)/g, "<li>$1</li>")
			.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
			.replace(/\n\n/g, "<br><br>")
			.replace(/\n/g, "<br>");
		return `<div class="markdown-content">${formatted}</div>`;
	};

	const pushError = content => {
		chatHistory.value.push({
			role: "assistant",
			content,
			timestamp: new Date().toLocaleString(),
			error: true
		});
		scrollToBottom();
	};

	const requireSession = () => {
		if (sessionStore.session?.sessionId) return true;
		pushError("请先输入两篇 Wikipedia URL 并加载比较会话。");
		return false;
	};

	const askQuestion = async () => {
		const question = userQuestion.value.trim();
		if (!question) {
			pushError("问题不能为空");
			return;
		}
		if (!requireSession()) return;

		chatHistory.value.push({
			role: "user",
			content: question,
			timestamp: new Date().toLocaleString()
		});
		userQuestion.value = "";
		isLoading.value = true;

		try {
			const response = await postJson("api/ask", {
				sessionId: sessionStore.session.sessionId,
				question
			});
			chatHistory.value.push({
				role: "assistant",
				content: formatAnalysisResult(response.answer),
				citations: response.citations || [],
				timestamp: new Date().toLocaleString()
			});
		} catch (error) {
			pushError(`请求失败: ${error.response?.data?.error || error.message || "未知错误"}`);
		} finally {
			isLoading.value = false;
			scrollToBottom();
		}
	};

	const handleAttributeComparison = async row => {
		if (!row) return;
		if (!requireSession()) return;

		isLoading.value = true;
		chatHistory.value.push({
			role: "assistant",
			content: `正在对比分析 <strong>${row.label}</strong> 属性...`,
			timestamp: new Date().toLocaleString()
		});

		try {
			const response = await postJson("api/analyze-attribute", {
				sessionId: sessionStore.session.sessionId,
				attributeId: row.id
			});
			chatHistory.value.push({
				role: "assistant",
				content: formatAnalysisResult(response.summary),
				citations: response.citations || [],
				timestamp: new Date().toLocaleString()
			});
		} catch (error) {
			pushError(`对比分析失败: ${error.response?.data?.error || error.message || "未知错误"}`);
		} finally {
			isLoading.value = false;
			scrollToBottom();
		}
	};
</script>

<style scoped>
	.main-container {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: #f5f7fa;
		overflow: hidden;
	}

	.chat-container {
		height: 38%;
		min-height: 170px;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		margin: 10px;
	}

	.chat-history {
		flex: 1;
		overflow-y: auto;
		padding: 16px;
		background: #ffffff;
		border-radius: 8px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
		scroll-behavior: smooth;
		border: 1px solid #e0e0e0;
	}

	.vis-container {
		height: 48%;
		min-height: 260px;
		padding: 10px;
		background: #ffffff;
		border-radius: 8px;
		margin: 0 10px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
		overflow: auto;
		border: 1px solid #e0e0e0;
	}

	.compare-table {
		width: 100%;
		height: 100%;
	}

	.input-area {
		min-height: 96px;
		padding: 12px;
		background: #ffffff;
		border-top: 1px solid #e0e0e0;
		flex-shrink: 0;
	}

	.message {
		margin-bottom: 14px;
		padding: 12px 14px;
		border-radius: 8px;
		line-height: 1.55;
		position: relative;
		max-width: 88%;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
	}

	.message.user {
		background: #e3f2fd;
		margin-left: auto;
		border: 1px solid #bbdefb;
	}

	.message.assistant {
		background: #f8f9fa;
		margin-right: auto;
		border: 1px solid #e0e0e0;
	}

	.message.error {
		background: #ffebee;
		border-left: 4px solid #f44336;
	}

	.message-content {
		word-wrap: break-word;
	}

	.input-container {
		display: flex;
		flex-direction: column;
		background: #ffffff;
		border-radius: 8px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		height: 100%;
		border: 1px solid #e0e0e0;
	}

	.input-container textarea {
		width: 100%;
		padding: 10px 12px;
		border: none;
		border-radius: 8px;
		resize: none;
		font-size: 14px;
		outline: none;
		background: #f9f9f9;
	}

	.button-container {
		display: flex;
		justify-content: flex-end;
		padding: 8px;
	}

	.button-container button {
		background: #2563eb;
		color: white;
		border: none;
		padding: 8px 18px;
		border-radius: 6px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
	}

	.button-container button:disabled {
		background: #b3c6e0;
		cursor: not-allowed;
	}

	.loading-indicator {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 15px;
		color: #666;
		font-size: 14px;
	}

	.loading-spinner {
		border: 3px solid rgba(66, 133, 244, 0.2);
		border-radius: 50%;
		border-top: 3px solid #4285f4;
		width: 20px;
		height: 20px;
		animation: spin 1s linear infinite;
		margin-right: 10px;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.markdown-content {
		line-height: 1.7;
		font-size: 14px;
		color: #333;
	}

	.markdown-content h1,
	.markdown-content h2,
	.markdown-content h3 {
		margin: 10px 0 8px;
		color: #1e293b;
	}
</style>
