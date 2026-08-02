<template>
	<section class="admin-panel">
		<header class="panel-header">
			<div>
				<h2>题目管理</h2>
				<p>管理 Q1-Q5 的生成结果、隐藏标准答案和冻结状态。</p>
			</div>
			<label class="material-select">
				材料
				<select v-model="selectedMaterial" :disabled="loading || saving">
					<option v-for="material in materials" :key="material.id" :value="material.id">
						{{ material.label }}
					</option>
				</select>
			</label>
		</header>

		<div v-if="message" class="notice success">{{ message }}</div>
		<div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>

		<div class="status-card">
			<div><strong>Material ID</strong><span>{{ questionPayload?.material_id || selectedMaterial }}</span></div>
			<div><strong>冻结状态</strong><span :class="questionPayload?.frozen ? 'frozen' : 'unfrozen'">{{ questionPayload?.frozen ? "已冻结" : "未冻结" }}</span></div>
			<div><strong>版本</strong><span>{{ questionPayload?.version ?? "—" }}</span></div>
			<div><strong>生成时间</strong><span>{{ questionPayload?.generated_at || "—" }}</span></div>
			<div><strong>冻结时间</strong><span>{{ questionPayload?.frozen_at || "—" }}</span></div>
		</div>

		<div v-if="loading" class="loading-state">正在加载题目...</div>

		<div v-else class="questions-list">
			<article v-for="question in questions" :key="question.question_id" class="question-card">
				<header>
					<span class="question-id">{{ question.question_id }}</span>
					<span class="question-type">{{ question.question_type || "未设置题型" }}</span>
				</header>
				<h3>{{ question.question_text || "未设置题干" }}</h3>
				<p v-if="question.understanding_target" class="target">理解目标：{{ question.understanding_target }}</p>
				<div class="gold-block">
					<strong>隐藏 gold atoms / reference answers（仅管理后台显示）</strong>
					<pre>{{ hiddenAnswerJson(question) }}</pre>
				</div>
			</article>
			<div v-if="!questions.length" class="empty-state">当前材料尚未保存 Q1-Q5。</div>
		</div>

		<section class="raw-json-card">
			<label for="raw-questions-json">从系统自动生成结果粘贴或由后续自动生成按钮填入</label>
			<textarea
				id="raw-questions-json"
				v-model="rawQuestions"
				rows="14"
				placeholder='{"material_id":"M1","questions":[...]}'
				:disabled="saving"></textarea>
			<div class="action-row">
				<button type="button" class="primary" :disabled="saving || !rawQuestions.trim()" @click="saveGeneratedQuestions">
					{{ savingAction === "generate" ? "正在保存..." : "保存本次生成结果" }}
				</button>
				<button type="button" :disabled="saving || questionPayload?.frozen" @click="freezeSelectedQuestions">
					{{ savingAction === "freeze" ? "正在冻结..." : "冻结题目" }}
				</button>
				<button type="button" :disabled="saving || !questionPayload?.frozen" @click="unfreezeSelectedQuestions">
					{{ savingAction === "unfreeze" ? "正在解冻..." : "解冻题目" }}
				</button>
			</div>
		</section>
	</section>
</template>

<script setup>
	import { computed, ref, watch } from "vue";
	import {
		adminFreezeQuestions,
		adminGenerateQuestions,
		adminQuestions,
		adminUnfreezeQuestions
	} from "@/experiment/experimentApi";

	const props = defineProps({
		token: {
			type: String,
			required: true
		}
	});

	const materials = [
		{ id: "M1", label: "M1：Economy of South Korea vs Economy of Japan" },
		{ id: "M2", label: "M2：India 2026 vs Indonesia 2026" }
	];

	const selectedMaterial = ref("M1");
	const questionPayload = ref(null);
	const rawQuestions = ref("");
	const loading = ref(false);
	const savingAction = ref("");
	const message = ref("");
	const errorMessage = ref("");

	const saving = computed(() => Boolean(savingAction.value));
	const questions = computed(() => questionPayload.value?.questions || []);

	const showError = error => {
		errorMessage.value = error.response?.data?.error || error.message || "操作失败，请稍后重试。";
	};

	const loadQuestions = async () => {
		loading.value = true;
		message.value = "";
		errorMessage.value = "";
		try {
			questionPayload.value = await adminQuestions(props.token, selectedMaterial.value);
		} catch (error) {
			questionPayload.value = null;
			showError(error);
		} finally {
			loading.value = false;
		}
	};

	watch(selectedMaterial, loadQuestions, { immediate: true });

	const saveGeneratedQuestions = async () => {
		if (!rawQuestions.value.trim()) return;
		savingAction.value = "generate";
		message.value = "";
		errorMessage.value = "";
		try {
			questionPayload.value = await adminGenerateQuestions(props.token, selectedMaterial.value, rawQuestions.value);
			rawQuestions.value = "";
			message.value = "已保存本次生成结果。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const freezeSelectedQuestions = async () => {
		savingAction.value = "freeze";
		message.value = "";
		errorMessage.value = "";
		try {
			questionPayload.value = await adminFreezeQuestions(props.token, selectedMaterial.value);
			message.value = "题目已冻结。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const unfreezeSelectedQuestions = async () => {
		savingAction.value = "unfreeze";
		message.value = "";
		errorMessage.value = "";
		try {
			questionPayload.value = await adminUnfreezeQuestions(props.token, selectedMaterial.value);
			message.value = "题目已解冻。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const hiddenAnswerJson = question => {
		const hiddenPayload = {
			gold_atoms: question.gold_atoms || [],
			canonical_answer: question.canonical_answer,
			accepted_variants: question.accepted_variants,
			source_evidence: question.source_evidence,
			source_ids: question.source_ids
		};
		return JSON.stringify(hiddenPayload, null, 2);
	};
</script>

<style scoped>
	.admin-panel {
		display: grid;
		gap: 20px;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		gap: 20px;
		align-items: flex-start;
	}

	h2 {
		margin: 0 0 8px;
		font-size: 28px;
		color: #172033;
	}

	p {
		margin: 0;
		color: #64748b;
	}

	.material-select {
		display: grid;
		gap: 8px;
		min-width: 280px;
		font-weight: 800;
		color: #334155;
	}

	select,
	textarea {
		border: 1px solid #cbd5e1;
		border-radius: 12px;
		padding: 10px 12px;
		font: inherit;
		background: #ffffff;
	}

	textarea {
		width: 100%;
		box-sizing: border-box;
		font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
		font-size: 13px;
		resize: vertical;
	}

	.status-card {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 12px;
		border: 1px solid #dbe4ee;
		border-radius: 16px;
		padding: 16px;
		background: #f8fafc;
	}

	.status-card div {
		display: grid;
		gap: 4px;
	}

	.status-card strong {
		font-size: 12px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
	}

	.status-card span {
		font-weight: 800;
		color: #172033;
		word-break: break-word;
	}

	.frozen {
		color: #b45309 !important;
	}

	.unfrozen {
		color: #047857 !important;
	}

	.questions-list {
		display: grid;
		gap: 14px;
	}

	.question-card,
	.raw-json-card,
	.empty-state,
	.loading-state,
	.notice {
		border: 1px solid #dbe4ee;
		border-radius: 16px;
		padding: 16px;
		background: #ffffff;
	}

	.question-card header {
		display: flex;
		gap: 10px;
		align-items: center;
		margin-bottom: 8px;
	}

	.question-id,
	.question-type {
		border-radius: 999px;
		padding: 4px 10px;
		font-size: 12px;
		font-weight: 900;
	}

	.question-id {
		background: #dbeafe;
		color: #1d4ed8;
	}

	.question-type {
		background: #f1f5f9;
		color: #334155;
	}

	h3 {
		margin: 0 0 10px;
		font-size: 18px;
		line-height: 1.45;
		color: #172033;
	}

	.target {
		margin-bottom: 12px;
	}

	.gold-block {
		display: grid;
		gap: 8px;
	}

	.gold-block strong,
	.raw-json-card label {
		font-weight: 900;
		color: #334155;
	}

	pre {
		max-height: 260px;
		overflow: auto;
		margin: 0;
		border-radius: 12px;
		padding: 12px;
		background: #0f172a;
		color: #e2e8f0;
		font-size: 12px;
		white-space: pre-wrap;
	}

	.raw-json-card {
		display: grid;
		gap: 12px;
	}

	.action-row {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
	}

	button {
		border: 1px solid #cbd5e1;
		border-radius: 12px;
		padding: 10px 14px;
		background: #ffffff;
		color: #172033;
		font-weight: 900;
		cursor: pointer;
	}

	button.primary {
		border-color: #2563eb;
		background: #2563eb;
		color: #ffffff;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.55;
	}

	.notice.success {
		border-color: #bbf7d0;
		background: #f0fdf4;
		color: #166534;
	}

	.notice.error {
		border-color: #fecaca;
		background: #fff7f7;
		color: #991b1b;
	}

	.empty-state,
	.loading-state {
		color: #64748b;
		text-align: center;
	}

	@media (max-width: 760px) {
		.panel-header {
			display: grid;
		}

		.material-select {
			min-width: 0;
		}
	}
</style>
