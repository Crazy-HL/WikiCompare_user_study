<template>
	<section class="chatgpt-condition">
		<div class="article-pane">
			<ParentComponent side="left" divId="chatgpt-left" selectContentClass="chatgpt-left-content" />
		</div>

		<div class="static-table-pane" aria-label="ChatGPT 条件静态输出与提问区">
			<div v-if="!staticRows.length" class="empty-static-table">
				管理员尚未冻结该材料的 ChatGPT 静态三栏表。
			</div>
			<div v-else class="gpt-table-output" aria-label="ChatGPT 生成的静态三栏表">
				<table class="gpt-markdown-table">
					<thead>
						<tr>
							<th>左侧</th>
							<th>比较项</th>
							<th>右侧</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(row, index) in staticRows" :key="row.id || `${row.label}-${index}`">
							<td>{{ sideValue(row, "left") }}</td>
							<td class="comparison-label">{{ row.label || `项目 ${index + 1}` }}</td>
							<td>{{ sideValue(row, "right") }}</td>
						</tr>
					</tbody>
				</table>
			</div>

			<form class="chatgpt-composer" @submit.prevent="askQuestion">
				<label class="sr-only" for="chatgpt-question">向系统提问</label>
				<textarea
					id="chatgpt-question"
					v-model="question"
					rows="1"
					placeholder="Message ChatGPT"
					:disabled="isLoading || !hasSession"></textarea>
				<button type="submit" :disabled="isLoading || !hasSession || !question.trim()" aria-label="发送问题">
					{{ isLoading ? "…" : "↑" }}
				</button>
				<p v-if="!hasSession" class="ask-note">材料会话加载完成后可提问。</p>
			</form>

			<div v-if="messages.length" class="answer-history" aria-live="polite">
				<div
					v-for="(message, index) in messages"
					:key="index"
					:class="['message', message.role, { error: message.error }]">
					<strong>{{ message.role === "user" ? "我的问题" : "系统回答" }}</strong>
					<p>{{ message.content }}</p>
					<ul v-if="message.citations?.length" class="citation-list">
						<li v-for="(citation, citationIndex) in message.citations" :key="citationIndex">
							{{ citation.label || citation.sourceIds?.join(", ") || "证据" }}
						</li>
					</ul>
				</div>
			</div>
		</div>

		<div class="article-pane">
			<ParentComponent side="right" divId="chatgpt-right" selectContentClass="chatgpt-right-content" />
		</div>
	</section>
</template>

<script setup>
	import { computed, ref, watch } from "vue";
	import ParentComponent from "@/components/compoents_base/ParentComponent.vue";
	import { postJson } from "@/api";
	import { sessionStore } from "@/js/sessionStore";

	const props = defineProps({
		frozenRows: {
			type: Array,
			default: () => []
		}
	});

	const question = ref("");
	const messages = ref([]);
	const isLoading = ref(false);
	const hasSession = computed(() => Boolean(sessionStore.session?.sessionId));
	const staticRows = computed(() => props.frozenRows || []);

	watch(
		() => sessionStore.session?.sessionId,
		() => {
			messages.value = [];
			question.value = "";
		}
	);

	const stringifyValue = value => {
		if (value === null || value === undefined || value === "") return "—";
		if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
			return String(value);
		}
		if (Array.isArray(value)) {
			return value.map(stringifyValue).join("; ");
		}
		if (value.display || value.rawText || value.raw || value.value) {
			return stringifyValue(value.display || value.rawText || value.raw || value.value);
		}
		return JSON.stringify(value);
	};

	const sideValue = (row, side) => {
		const sideData = row?.visualization?.[side] || row?.[side] || {};
		if (Array.isArray(sideData.values) && sideData.values.length) {
			return sideData.values.map(value => stringifyValue(value)).join("; ");
		}
		return stringifyValue(sideData.raw || sideData.value || sideData.text || row?.[`${side}Value`]);
	};

	const conversationHistory = () => messages.value
		.filter(message => !message.error)
		.map(message => ({
			role: message.role === "user" ? "user" : "assistant",
			content: message.content
		}));

	const askQuestion = async () => {
		const text = question.value.trim();
		if (!text || !hasSession.value) return;
		const priorConversationHistory = conversationHistory();
		messages.value.push({ role: "user", content: text });
		question.value = "";
		isLoading.value = true;
		try {
			const response = await postJson("api/ask", {
				sessionId: sessionStore.session.sessionId,
				question: text,
				conversationHistory: priorConversationHistory
			});
			messages.value.push({
				role: "assistant",
				content: response.answer || "",
				citations: response.citations || []
			});
		} catch (error) {
			messages.value.push({
				role: "assistant",
				content: `请求失败：${error.response?.data?.error || error.message || "未知错误"}`,
				error: true
			});
		} finally {
			isLoading.value = false;
		}
	};
</script>

<style scoped>
	.chatgpt-condition {
		display: grid;
		grid-template-columns: minmax(250px, 0.9fr) minmax(360px, 1.1fr) minmax(250px, 0.9fr);
		gap: 8px;
		height: 100%;
		min-height: 0;
		padding: 8px;
		box-sizing: border-box;
		background: #ffffff;
	}

	.article-pane,
	.static-table-pane {
		min-width: 0;
		min-height: 0;
		overflow: auto;
		border: 1px solid rgba(226, 232, 240, 0.9);
		border-radius: 6px;
		background: #ffffff;
	}

	.static-table-pane {
		display: flex;
		flex-direction: column;
	}

	.empty-static-table {
		margin: 14px;
		padding: 18px;
		border: 1px dashed #cbd5e1;
		border-radius: 12px;
		background: #f8fafc;
		color: #475569;
		line-height: 1.6;
	}

	.gpt-table-output {
		flex: 1;
		overflow-x: auto;
		margin: 14px 14px 8px;
		color: #0d0d0d;
		font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
		font-size: 14px;
		line-height: 1.55;
	}

	.gpt-markdown-table {
		width: 100%;
		border-collapse: collapse;
		border-spacing: 0;
		font-size: 14px;
		line-height: 1.55;
	}

	.gpt-markdown-table th,
	.gpt-markdown-table td {
		vertical-align: top;
		padding: 8px 12px;
		border: 1px solid #d9d9e3;
		text-align: left;
		font-weight: 400;
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}

	.gpt-markdown-table th {
		background: #f7f7f8;
		color: #0d0d0d;
		font-weight: 600;
	}

	.gpt-markdown-table tbody tr:nth-child(even) td {
		background: #fcfcfd;
	}

	.comparison-label {
		font-weight: 400;
		color: #0d0d0d;
	}

	.chatgpt-composer {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 8px;
		align-items: end;
		margin: auto 14px 14px;
		padding: 8px 8px 8px 14px;
		border: 1px solid #d9d9e3;
		border-radius: 24px;
		background: #ffffff;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	textarea {
		width: 100%;
		box-sizing: border-box;
		resize: none;
		border: 0;
		outline: 0;
		padding: 8px 0;
		font: inherit;
		line-height: 1.45;
	}

	button {
		width: 34px;
		height: 34px;
		border: 0;
		border-radius: 999px;
		padding: 0;
		background: #0d0d0d;
		color: #ffffff;
		font-weight: 900;
		cursor: pointer;
	}

	button:disabled {
		background: #94a3b8;
		cursor: not-allowed;
	}

	.ask-note {
		margin: 0;
		color: #64748b;
		font-size: 12px;
	}

	.answer-history {
		display: grid;
		gap: 10px;
		margin: 14px;
	}

	.message {
		padding: 11px 12px;
		border-radius: 12px;
		background: #eff6ff;
		color: #1e293b;
		font-size: 13px;
		line-height: 1.55;
	}

	.message.user {
		background: #ecfdf5;
	}

	.message.error {
		background: #fef2f2;
		color: #991b1b;
	}

	.message p {
		white-space: pre-wrap;
		margin: 5px 0 0;
	}

	.citation-list {
		margin: 8px 0 0;
		padding-left: 18px;
		color: #475569;
	}

	@media (max-width: 1100px) {
		.chatgpt-condition {
			grid-template-columns: 1fr;
			grid-template-rows: minmax(360px, 48vh) minmax(460px, auto) minmax(360px, 48vh);
			overflow: auto;
		}
	}
</style>
