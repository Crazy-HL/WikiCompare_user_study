<template>
	<div class="main-container" :class="{ 'screenshot-mode': screenshotMode }">
		<!-- ✅ 新增：截图模式切换按钮（可选） -->
		<button
			class="screenshot-toggle-btn"
			@click="screenshotMode = !screenshotMode">
			{{ screenshotMode ? "退出截图模式" : "进入截图模式" }}
		</button>

		<!-- 聊天区（截图模式下隐藏） -->
		<div v-if="!screenshotMode" class="chat-container">
			<div class="chat-history">
				<div
					v-for="(message, index) in chatHistory"
					:key="index"
					:class="['message', message.role, { error: message.error }]">
					<div class="message-content" v-html="message.content"></div>
					<CausalFlowChart
						v-if="message.isCausalFlow"
						:chains="message.causalChains"
						class="causal-flow-container" />
				</div>
				<div v-if="isLoading" class="loading-indicator">
					<div class="loading-spinner"></div>
					正在处理中...
				</div>
				<div v-if="showSuggestedQuestion" class="suggested-question">
					<div class="suggestion-text">建议深入分析的问题：</div>
					<div class="suggestion-content" @click="useSuggestedQuestion">
						{{ suggestedQuestion }}
					</div>
				</div>
			</div>
		</div>

		<!-- 对比表格区域 -->
		<div class="vis-container">
			<CompareTable
				class="compare-table"
				:div1-raw-data="div1RawData"
				:div3-raw-data="div3RawData"
				@compareAttribute="handleAttributeComparison" />
		</div>

		<!-- 输入区（截图模式下隐藏） -->
		<div v-if="!screenshotMode" class="input-area">
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
	import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
	import bus from "@/js/eventBus.js";
	import CompareTable from "@/components/compoents_base/CompareTable.vue";
	import CausalFlowChart from "@/components/compoents_base/CausalFlowChart.vue";

	const PRESERVED_FIELDS_BY_SECTION = {
		Statistics: [
			"Population",
			"GDP",
			"GDP rank",
			"GDP growth",
			"GDP per capita",
			"GDP per capita rank",
			"GDP by sector",
			"Inflation (CPI)",
			"Population below poverty line",
			"Gini coefficient",
			"Human Development Index",
			"Corruption Perceptions Index",
			"Labor force",
			"Labor force by occupation",
			"Unemployment",
			"Average gross salary",
			"Average net salary",
			"Main industries"
		],
		"Public finances": [
			"Government debt",
			"Foreign reserves",
			"Budget balance",
			"Revenues",
			"Expenses",
			"Economic aid",
			"Credit rating"
		]
	};

	const userQuestion = ref("");
	const chatHistory = ref([]);
	const selectText2 = ref("");
	const selectText3 = ref("");
	const div1RawData = ref(null);
	const div3RawData = ref(null);
	const isLoading = ref(false);
	const div1InfoboxData = ref(null);
	const div3InfoboxData = ref(null);
	const showSuggestedQuestion = ref(false);
	const suggestedQuestion = ref("");
	const currentFieldKey = ref("");
	const leftData = ref(null);
	const rightData = ref(null);

	/* ✅ 新增：截图模式开关 */
	const screenshotMode = ref(false);

	const loadChatHistory = () => {
		const saved = localStorage.getItem("chatHistory");
		if (saved) {
			try {
				// chatHistory.value = JSON.parse(saved);
			} catch (e) {
				console.error("加载聊天记录失败:", e);
			}
		}
	};

	watch(
		chatHistory,
		newVal => {
			localStorage.setItem("chatHistory", JSON.stringify(newVal));
		},
		{ deep: true }
	);

	const scrollToBottom = () => {
		nextTick(() => {
			const container = document.querySelector(".chat-history");
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
		});
	};

	const getLastAnalysis = () => {
		const reversed = [...chatHistory.value].reverse();
		const lastAssistantMsg = reversed.find(
			msg => msg.role === "assistant" && !msg.error
		);
		return lastAssistantMsg ? lastAssistantMsg.content : "";
	};

	const handleDiv1Event = data => handleSelection(data, "div1");
	const handleDiv3Event = data => handleSelection(data, "div3");

	onMounted(() => {
		loadChatHistory();
		bus.on("div1_Event", handleDiv1Event);
		bus.on("div3_Event", handleDiv3Event);
		bus.on("div1_InfoboxData", data => {
			div1InfoboxData.value = data;
		});
		bus.on("div3_InfoboxData", data => {
			div3InfoboxData.value = data;
		});

		/* ✅ 新增：允许按 F9 快捷键切换截图模式 */
		window.addEventListener("keydown", e => {
			if (e.key === "F9") screenshotMode.value = !screenshotMode.value;
		});
	});

	onUnmounted(() => {
		bus.off("div1_Event", handleDiv1Event);
		bus.off("div3_Event", handleDiv3Event);
		bus.off("div1_InfoboxData");
		bus.off("div3_InfoboxData");
	});

	function handleSelection(data, source) {
		const plainText = getPlainTextFromSelection(data.content);
		if (source === "div1") {
			selectText2.value = plainText;
			div1RawData.value = data.content;
		} else if (source === "div3") {
			selectText3.value = plainText;
			div3RawData.value = data.content;
		}
	}

	function getPlainTextFromSelection(htmlContent) {
		const container = document.createElement("div");
		container.innerHTML = htmlContent;
		return container.innerText || container.textContent || "";
	}

	const formatAnalysisResult = text => {
		if (!text) return "";

		text = text
			.replace(/^# (.*$)/gm, "<h1>$1</h1>")
			.replace(/^## (.*$)/gm, "<h2>$1</h2>")
			.replace(/^### (.*$)/gm, "<h3>$1</h3>")
			.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
			.replace(/\*(.*?)\*/g, "<em>$1</em>")
			.replace(/`(.*?)`/g, "<code>$1</code>")
			.replace(/!\[(.*?)\]\((.*?)\)/g, '<img alt="$1" src="$2">')
			.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
			.replace(/(?:^|\n)\d+\.\s+(.*)/g, "<li>$1</li>")
			.replace(/(?:^|\n)-\s+(.*)/g, "<li>$1</li>")
			.replace(/(?:^|\n)\>\s+(.*)/g, "<blockquote>$1</blockquote>")
			.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
			.replace(/\n\n/g, "<br><br>")
			.replace(/\n/g, "<br>");

		return `<div class="markdown-content">${text}</div>`;
	};

	const extractEssentialData = fieldData => {
		if (!fieldData) return null;

		const essential = {
			value: fieldData.value,
			type: fieldData.type
		};

		if (fieldData.unit) essential.unit = fieldData.unit;
		if (fieldData.currency) essential.currency = fieldData.currency;
		if (fieldData.extracted) essential.raw = fieldData.raw;

		return essential;
	};

	const simplifyInfobox = infobox => {
		if (!infobox) return {};

		const result = {
			title: infobox.title,
			type: infobox.type
		};

		if (infobox.sections) {
			result.sections = {};

			Object.entries(infobox.sections).forEach(([sectionName, sectionData]) => {
				if (PRESERVED_FIELDS_BY_SECTION[sectionName]) {
					result.sections[sectionName] = {};

					PRESERVED_FIELDS_BY_SECTION[sectionName].forEach(fieldName => {
						if (sectionData[fieldName]) {
							if (Array.isArray(sectionData[fieldName])) {
								result.sections[sectionName][fieldName] = sectionData[
									fieldName
								].map(item => extractEssentialData(item));
							} else {
								result.sections[sectionName][fieldName] = extractEssentialData(
									sectionData[fieldName]
								);
							}
						}
					});
				}
			});
		}
		return result;
	};

	const parseCausalChains = text => {
		const chains = [];
		const countries = text.split("##").filter(s => s.trim());

		countries.forEach(countrySection => {
			const countryMatch = countrySection.match(/(韩国|日本)/);
			if (!countryMatch) return;

			const country = countryMatch[0] === "韩国" ? "korea" : "japan";
			const chainContent = countrySection.replace(/^.*?\n/, "").trim();

			const steps = chainContent
				.split("→")
				.map(step => {
					const cleanStep = step.trim();
					const evidenceMatch = cleanStep.match(/\((.*?)\)/);
					const textPart = evidenceMatch
						? cleanStep.replace(evidenceMatch[0], "").trim()
						: cleanStep;

					return {
						text: textPart,
						evidence: evidenceMatch ? evidenceMatch[1] : null
					};
				})
				.filter(step => step.text);

			if (steps.length > 0) {
				chains.push({
					country,
					steps: steps.slice(0, 6)
				});
			}
		});

		return chains;
	};

	const askQuestion = async () => {
		if (!userQuestion.value.trim()) {
			chatHistory.value.push({
				role: "assistant",
				content: "问题不能为空",
				timestamp: new Date().toLocaleString(),
				error: true
			});
			return;
		}

		const question = userQuestion.value;
		chatHistory.value.push({
			role: "user",
			content: question,
			timestamp: new Date().toLocaleString()
		});
		userQuestion.value = "";
		showSuggestedQuestion.value = false;

		isLoading.value = true;

		try {
			if (
				currentFieldKey.value &&
				question.includes("请结合其他属性深入分析得出上述结论的原因")
			) {
				await api.post(
					"compare_attributes",
					{
						chartData: {
							leftData: leftData.value,
							rightData: rightData.value,
							leftTitle: "当前选择",
							rightTitle: "对比选择",
							fieldKey: currentFieldKey.value,
							leftInfobox: simplifyInfobox(div1InfoboxData.value),
							rightInfobox: simplifyInfobox(div3InfoboxData.value)
						},
						chartType: "comparison",
						followUp: true,
						previousAnalysis: getLastAnalysis()
					},
					response => {
						const res = JSON.parse(response.analysis);
						chatHistory.value.push({
							role: "assistant",
							content: "以下是因果分析：",
							isCausalFlow: true,
							causalChains: res,
							timestamp: new Date().toLocaleString()
						});
						scrollToBottom();
					},
					error => {
						throw error;
					}
				);
			} else {
				await api.post(
					"ask_infobox",
					{
						question: question,
						leftInfobox: simplifyInfobox(div1InfoboxData.value),
						rightInfobox: simplifyInfobox(div3InfoboxData.value)
					},
					response => {
						const formattedAnswer = formatAnalysisResult(response.answer);
						chatHistory.value.push({
							role: "assistant",
							content: formattedAnswer,
							timestamp: new Date().toLocaleString()
						});
						scrollToBottom();
					},
					error => {
						throw error;
					}
				);
			}
		} catch (error) {
			console.error("请求失败:", error);
			chatHistory.value.push({
				role: "assistant",
				content: `请求失败: ${error.message || "未知错误"}`,
				timestamp: new Date().toLocaleString(),
				error: true
			});
		} finally {
			isLoading.value = false;
			scrollToBottom();
		}
	};

	const useSuggestedQuestion = () => {
		userQuestion.value = suggestedQuestion.value;
		showSuggestedQuestion.value = false;
		nextTick(() => {
			document.querySelector(".input-container textarea").focus();
		});
	};

	const handleAttributeComparison = async ({
		fieldKey,
		leftData: incomingLeftData,
		rightData: incomingRightData,
		leftTitle,
		rightTitle,
		fieldType,
		fieldLabel
	}) => {
		if (!incomingLeftData || !incomingRightData) {
			chatHistory.value.push({
				role: "assistant",
				content: "请先选择要对比的数据",
				timestamp: new Date().toLocaleString(),
				error: true
			});
			return;
		}

		leftData.value = incomingLeftData;
		rightData.value = incomingRightData;
		currentFieldKey.value = fieldKey;

		isLoading.value = true;

		try {
			chatHistory.value.push({
				role: "assistant",
				content: `正在对比分析<strong>${fieldKey}</strong>属性...`,
				timestamp: new Date().toLocaleString()
			});

			const requestPayload = {
				chartData: {
					leftData: leftData.value,
					rightData: rightData.value,
					leftTitle,
					rightTitle,
					fieldKey,
					fieldType,
					allFields: Object.keys({
						...div1InfoboxData.value,
						...div3InfoboxData.value
					}),
					leftInfobox: simplifyInfobox(div1InfoboxData.value),
					rightInfobox: simplifyInfobox(div3InfoboxData.value)
				},
				chartType: "comparison"
			};

			await api.post(
				"compare_attributes",
				requestPayload,
				response => {
					console.log("resp:", response);
					const formattedAnalysis = formatAnalysisResult(response.analysis);
					chatHistory.value.push({
						role: "assistant",
						content: formattedAnalysis,
						timestamp: new Date().toLocaleString()
					});

					suggestedQuestion.value = `请结合其他属性深入分析得出上述结论的原因`;
					showSuggestedQuestion.value = true;
					scrollToBottom();
				},
				error => {
					throw error;
				}
			);
		} catch (error) {
			console.error("对比分析失败:", error);
			chatHistory.value.push({
				role: "assistant",
				content: `对比分析失败: ${error.message || "未知错误"}`,
				timestamp: new Date().toLocaleString(),
				error: true
			});
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
		height: 100vh;
		background: #f5f7fa;
		overflow: hidden;
		position: relative;
	}

	/* ✅ 新增：截图模式样式 */
	.screenshot-mode {
		background: #fff;
	}

	.screenshot-mode .vis-container {
		height: 100vh !important;
		min-height: 100vh !important;
		margin: 0 !important;
		padding: 0 !important;
		border: none !important;
		box-shadow: none !important;
		border-radius: 0 !important;
	}

	.screenshot-mode .compare-table {
		width: 100% !important;
		height: 100% !important;
	}

	/* ✅ 新增：截图按钮样式 */
	.screenshot-toggle-btn {
		position: absolute;
		top: 10px;
		right: 10px;
		z-index: 999;
		padding: 8px 12px;
		background: #4285f4;
		color: #fff;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 13px;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
	}

	.screenshot-toggle-btn:hover {
		background: #3367d6;
	}

	.chat-container {
		height: 50vh;
		min-height: 20vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		margin: 10px;
	}

	.chat-history {
		flex: 1;
		overflow-y: auto;
		padding: 20px;
		background: #ffffff;
		border-radius: 12px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
		scroll-behavior: smooth;
		border: 1px solid #e0e0e0;
	}

	.vis-container {
		height: 70vh;
		min-height: 50vh;
		padding: 10px;
		background: #ffffff;
		border-radius: 12px;
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
		height: 8vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 10px;
		background: #ffffff;
		box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.05);
	}

	.input-container {
		display: flex;
		width: 95%;
		align-items: center;
	}

	textarea {
		flex: 1;
		resize: none;
		border-radius: 8px;
		border: 1px solid #ccc;
		padding: 8px;
		font-size: 14px;
		outline: none;
		transition: all 0.3s;
	}

	textarea:focus {
		border-color: #4285f4;
		box-shadow: 0 0 4px rgba(66, 133, 244, 0.3);
	}

	.button-container {
		margin-left: 10px;
	}

	button {
		padding: 8px 16px;
		background: #4285f4;
		color: #fff;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		transition: background 0.3s;
	}

	button:hover {
		background: #3367d6;
	}

	.message {
		margin-bottom: 12px;
		padding: 8px 12px;
		border-radius: 10px;
		max-width: 90%;
		word-break: break-word;
		line-height: 1.6;
	}

	.message.user {
		background: #e3f2fd;
		align-self: flex-end;
		margin-left: auto;
	}

	.message.assistant {
		background: #f1f8e9;
		align-self: flex-start;
	}

	.message.error {
		background: #ffebee;
		color: #c62828;
	}

	.message-content {
		font-size: 14px;
	}

	.loading-indicator {
		display: flex;
		align-items: center;
		color: #888;
		font-size: 13px;
		margin-top: 8px;
	}

	.loading-spinner {
		width: 14px;
		height: 14px;
		margin-right: 6px;
		border: 2px solid #ccc;
		border-top-color: #4285f4;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.suggested-question {
		margin-top: 12px;
		background: #fffde7;
		padding: 8px 12px;
		border-left: 4px solid #fbc02d;
		border-radius: 4px;
		cursor: pointer;
	}

	.suggested-question:hover {
		background: #fff9c4;
	}
</style>
