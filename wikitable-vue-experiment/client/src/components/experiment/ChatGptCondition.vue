<template>
	<section class="chatgpt-condition">
		<div class="article-pane">
			<ParentComponent side="left" divId="chatgpt-left" selectContentClass="chatgpt-left-content" />
		</div>

		<div class="static-table-pane">
			<div class="table-heading">
				<h2>静态三栏表</h2>
				<p>本阶段材料加载后，表格内容保持固定。</p>
			</div>

			<div v-if="!staticRows.length" class="empty-static-table">
				管理员尚未冻结该材料的 ChatGPT 静态三栏表。
			</div>
			<div v-else class="static-table-wrapper">
				<table>
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
							<td class="label-cell">{{ row.label || `项目 ${index + 1}` }}</td>
							<td>{{ sideValue(row, "right") }}</td>
						</tr>
					</tbody>
				</table>
			</div>

			<form class="ask-box" @submit.prevent="askQuestion">
				<label for="chatgpt-question">向系统提问</label>
				<textarea
					id="chatgpt-question"
					v-model="question"
					rows="3"
					placeholder="请输入与当前两篇材料有关的问题"
					:disabled="isLoading || !hasSession"></textarea>
				<button type="submit" :disabled="isLoading || !hasSession || !question.trim()">
					{{ isLoading ? "处理中..." : "发送问题" }}
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

	const question = ref("");
	const messages = ref([]);
	const isLoading = ref(false);
	const hasSession = computed(() => Boolean(sessionStore.session?.sessionId));
	const staticRows = computed(() => sessionStore.session?.rankedRows || []);

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
		messages.value.push({ role: "user", content: text });
		question.value = "";
		isLoading.value = true;
		try {
			const response = await postJson("api/ask", {
				sessionId: sessionStore.session.sessionId,
				question: text,
				conversationHistory: conversationHistory()
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
		gap: 10px;
		height: 100%;
		min-height: 0;
		padding: 10px;
		box-sizing: border-box;
		background: #eef3f8;
	}

	.article-pane,
	.static-table-pane {
		min-width: 0;
		min-height: 0;
		overflow: auto;
		border: 1px solid rgba(190, 201, 216, 0.82);
		border-radius: 8px;
		background: #ffffff;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 10px 24px rgba(15, 23, 42, 0.06);
	}

	.table-heading {
		position: sticky;
		top: 0;
		z-index: 1;
		padding: 14px;
		border-bottom: 1px solid #e2e8f0;
		background: rgba(255, 255, 255, 0.96);
	}

	h2 {
		margin: 0 0 4px;
		color: #172033;
		font-size: 18px;
	}

	.table-heading p {
		margin: 0;
		color: #64748b;
		font-size: 12px;
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

	.static-table-wrapper {
		overflow: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
		color: #243447;
	}

	th,
	td {
		vertical-align: top;
		padding: 9px 10px;
		border-bottom: 1px solid #e2e8f0;
	}

	th {
		position: sticky;
		top: 73px;
		background: #f8fafc;
		color: #475569;
		font-size: 11px;
		text-align: left;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.label-cell {
		font-weight: 780;
		color: #1d4ed8;
	}

	.ask-box {
		display: grid;
		gap: 9px;
		margin: 14px;
		padding: 14px;
		border: 1px solid #dbe4ee;
		border-radius: 12px;
		background: #f8fafc;
	}

	.ask-box label {
		font-weight: 800;
		color: #334155;
	}

	textarea {
		width: 100%;
		box-sizing: border-box;
		resize: vertical;
		border: 1px solid #cbd5e1;
		border-radius: 10px;
		padding: 9px;
		font: inherit;
		line-height: 1.45;
	}

	button {
		justify-self: end;
		border: 0;
		border-radius: 10px;
		padding: 9px 14px;
		background: #2563eb;
		color: #ffffff;
		font-weight: 800;
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
