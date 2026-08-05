<template>
	<section class="admin-panel">
		<header class="panel-header">
			<div>
				<h2>题目与静态三栏表管理</h2>
				<p>管理 Q1-Q5 的生成结果、隐藏标准答案、生成提示词、冻结状态，以及 ChatGPT 条件使用的冻结静态三栏表。</p>
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
			<div><strong>题目冻结状态</strong><span :class="questionsFrozen ? 'frozen' : 'unfrozen'">{{ questionsFrozen ? "已冻结" : "未冻结" }}</span></div>
			<div><strong>题目版本</strong><span>{{ questionPayload?.version ?? "—" }}</span></div>
			<div><strong>题目冻结时间</strong><span>{{ questionPayload?.frozen_at || "—" }}</span></div>
			<div><strong>静态表冻结状态</strong><span :class="staticTablePayload?.frozen ? 'frozen' : 'unfrozen'">{{ staticTablePayload?.frozen ? "已冻结" : "未冻结" }}</span></div>
			<div><strong>静态表版本</strong><span>{{ staticTablePayload?.version ?? "—" }}</span></div>
		</div>

		<section class="question-actions-card">
			<div>
				<h3>题目生成与冻结</h3>
				<p>自动生成会覆盖当前未冻结题目；冻结后参与者才会看到固定题目。若要修改已冻结题目，请先解冻。</p>
			</div>
			<div class="action-row">
				<button type="button" class="primary" :disabled="saving || questionsFrozen" @click="autoGenerateQuestions">
					{{ savingAction === "auto-generate" ? "正在自动生成..." : questions.length ? "重新自动生成题目" : "自动生成题目" }}
				</button>
				<button type="button" :disabled="saving || questionsFrozen || !questions.length" @click="freezeSelectedQuestions">
					{{ savingAction === "freeze" ? "正在冻结..." : "冻结题目" }}
				</button>
				<button type="button" :disabled="saving || !questionsFrozen" @click="unfreezeSelectedQuestions">
					{{ savingAction === "unfreeze" ? "正在解冻..." : "解冻题目" }}
				</button>
			</div>
		</section>

		<section class="prompt-card">
			<header>
				<h3>生成提示词</h3>
				<p>这里给研究者查看自动生成题目、隐藏标准答案和 ChatGPT 静态三栏表时实际使用/保存的 prompt。旧版本如果没有记录，需要重新生成后才会显示完整 prompt。</p>
			</header>
			<div class="prompt-grid">
				<details :open="Boolean(staticTablePromptInfo?.chatgpt_condition_control_prompt)">
					<summary>提示词 0：ChatGPT 条件控制指令</summary>
					<pre>{{ staticTablePromptInfo?.chatgpt_condition_control_prompt?.text || "旧版本没有保存 ChatGPT 条件控制指令；请重新生成 ChatGPT 三栏表后查看。" }}</pre>
				</details>
				<details :open="Boolean(staticTablePromptInfo)">
					<summary>提示词 1：ChatGPT 静态三栏表生成</summary>
					<pre>{{ staticTablePromptInfo?.static_table_prompt?.user || "旧版本没有保存静态三栏表生成提示词；请重新生成 ChatGPT 三栏表后查看。" }}</pre>
				</details>
				<details :open="Boolean(promptInfo)">
					<summary>提示词 2：生成五个双文档比较问题</summary>
					<pre>{{ promptInfo?.question_prompt?.user || "旧版本没有保存题目生成提示词；请重新自动生成题目后查看。" }}</pre>
				</details>
				<details :open="Boolean(promptInfo?.validation_prompt)">
					<summary>提示词 3：验证问题是否合理</summary>
					<pre>{{ promptInfo?.validation_prompt?.user || "旧版本没有保存题目验证提示词；请重新自动生成题目后查看。" }}</pre>
				</details>
				<details>
					<summary>技术信息：题目 System Prompt</summary>
					<pre>{{ promptInfo?.question_prompt?.system || "旧版本没有保存题目 System Prompt；请重新自动生成题目后查看。" }}</pre>
				</details>
				<details>
					<summary>技术信息：静态三栏表 System Prompt</summary>
					<pre>{{ staticTablePromptInfo?.static_table_prompt?.system || "旧版本没有保存静态三栏表 System Prompt；请重新生成 ChatGPT 三栏表后查看。" }}</pre>
				</details>
				<div class="prompt-note">
					<strong>隐藏标准答案说明</strong>
					<p>{{ promptInfo?.answer_prompt?.note || "当前系统在同一次模型请求中共同生成参与者题目和管理员隐藏标准答案；没有单独的第二次答案生成 prompt。" }}</p>
				</div>
			</div>
		</section>

		<div v-if="loading" class="loading-state">正在加载配置...</div>

		<div v-else class="questions-list">
			<article v-for="question in questions" :key="question.question_id" class="question-card">
				<header>
					<div>
						<span class="question-id">{{ question.question_id }}</span>
						<span class="question-type">{{ question.question_type || "未设置题型" }}</span>
					</div>
					<div class="card-actions">
						<button v-if="!editingQuestions[question.question_id]" type="button" :disabled="saving || questionsFrozen" @click="startEditQuestion(question)">编辑</button>
						<button v-if="editingQuestions[question.question_id]" type="button" :disabled="saving" @click="cancelEditQuestion(question.question_id)">取消</button>
						<button v-if="editingQuestions[question.question_id]" type="button" class="primary" :disabled="saving || questionsFrozen" @click="saveQuestionEdit(question)">
							{{ savingAction === `save-question-${question.question_id}` ? "正在保存..." : "保存本题修改" }}
						</button>
					</div>
				</header>

				<div v-if="editingQuestions[question.question_id]" class="question-edit-form">
					<label>题目类型<input v-model="editingQuestions[question.question_id].question_type" :disabled="saving || questionsFrozen" /></label>
					<label>题目文本<textarea v-model="editingQuestions[question.question_id].question_text" rows="3" :disabled="saving || questionsFrozen"></textarea></label>
					<label>答题格式<textarea v-model="editingQuestions[question.question_id].answer_format" rows="2" :disabled="saving || questionsFrozen"></textarea></label>
					<label>理解目标<textarea v-model="editingQuestions[question.question_id].understanding_target" rows="2" :disabled="saving || questionsFrozen"></textarea></label>
					<label>固定选项（每行或逗号分隔一个，可留空）<textarea v-model="editingQuestions[question.question_id].answer_options_text" rows="2" :disabled="saving || questionsFrozen"></textarea></label>

					<section class="atom-editor">
						<header>
							<strong>隐藏标准答案 / 评分点</strong>
							<button type="button" :disabled="saving || questionsFrozen" @click="addGoldAtom(question.question_id)">添加评分点</button>
						</header>
						<div v-for="(atom, atomIndex) in editingQuestions[question.question_id].gold_atoms" :key="atom.draft_id" class="atom-edit-card">
							<div class="atom-edit-header">
								<strong>评分点 {{ atomIndex + 1 }}</strong>
								<button type="button" :disabled="saving || questionsFrozen || editingQuestions[question.question_id].gold_atoms.length <= 1" @click="removeGoldAtom(question.question_id, atomIndex)">删除</button>
							</div>
							<label>评分点 ID<input v-model="atom.atom_id" :disabled="saving || questionsFrozen" /></label>
							<label>评分要求<textarea v-model="atom.requirement" rows="2" :disabled="saving || questionsFrozen"></textarea></label>
							<label>标准答案<textarea v-model="atom.canonical_answer" rows="3" :disabled="saving || questionsFrozen"></textarea></label>
							<label>允许等价表达（每行或逗号分隔一个）<textarea v-model="atom.accepted_variants_text" rows="2" :disabled="saving || questionsFrozen"></textarea></label>
							<label>来源编号 source_ids（每行或逗号分隔一个）<textarea v-model="atom.source_ids_text" rows="2" :disabled="saving || questionsFrozen"></textarea></label>
							<label>单位要求<input v-model="atom.required_unit" :disabled="saving || questionsFrozen" /></label>
							<label>时间范围要求<input v-model="atom.required_time_scope" :disabled="saving || questionsFrozen" /></label>
						</div>
					</section>
				</div>

				<div v-else>
					<h3>{{ question.question_text || "未设置题干" }}</h3>
					<dl class="question-meta">
						<div v-if="question.answer_format"><dt>答题格式</dt><dd>{{ question.answer_format }}</dd></div>
						<div v-if="question.understanding_target"><dt>理解目标</dt><dd>{{ question.understanding_target }}</dd></div>
						<div v-if="question.answer_options?.length"><dt>固定选项</dt><dd>{{ question.answer_options.join(" / ") }}</dd></div>
					</dl>
					<div class="gold-block">
						<strong>隐藏标准答案 / 评分点（仅管理后台显示）</strong>
						<div v-if="goldAtoms(question).length" class="gold-atom-list">
							<div v-for="atom in goldAtoms(question)" :key="atom.atom_id || atom.canonical_answer" class="gold-atom-card">
								<div class="atom-title">{{ atom.atom_id || "评分点" }}</div>
								<p v-if="atom.requirement"><strong>评分要求：</strong>{{ atom.requirement }}</p>
								<p v-if="atom.canonical_answer"><strong>标准答案：</strong>{{ atom.canonical_answer }}</p>
								<p v-if="atom.accepted_variants?.length"><strong>等价表达：</strong>{{ atom.accepted_variants.join("；") }}</p>
								<p v-if="atom.required_unit"><strong>单位：</strong>{{ atom.required_unit }}</p>
								<p v-if="atom.required_time_scope"><strong>时间范围：</strong>{{ atom.required_time_scope }}</p>
								<div v-if="atom.source_ids?.length" class="source-chip-row">
									<span v-for="sourceId in atom.source_ids" :key="sourceId" class="source-chip">{{ sourceId }}</span>
								</div>
							</div>
						</div>
						<div v-else class="empty-inline">当前题目没有隐藏标准答案。</div>
					</div>
				</div>
			</article>
			<div v-if="!questions.length" class="empty-state">当前材料尚未保存 Q1-Q5。请先点击“自动生成题目”。</div>
		</div>

		<section class="static-table-card">
			<header>
				<div>
					<h3>ChatGPT 静态三栏表真实输出</h3>
					<p>这里直接展示系统根据当前材料生成给 ChatGPT 条件参与者看的三栏表。保存并冻结后，参与者只会看到这个冻结版本。</p>
				</div>
			</header>
			<div class="action-row">
				<button type="button" class="primary" :disabled="saving || staticTablePayload?.frozen" @click="generateStaticTableRows">
					{{ savingAction === "generate-static" ? "正在生成..." : staticTableDraftRows.length ? "重新生成 ChatGPT 三栏表" : "生成 ChatGPT 三栏表" }}
				</button>
				<button type="button" :disabled="saving || staticTablePayload?.frozen" @click="addStaticTableRow">新增一行</button>
				<button type="button" :disabled="saving || staticTablePayload?.frozen || !staticTableDraftRows.length" @click="saveStaticTableRows">
					{{ savingAction === "save-static" ? "正在保存..." : "保存表格修改" }}
				</button>
				<button type="button" :disabled="saving || staticTablePayload?.frozen || !staticTableDraftRows.length" @click="freezeStaticTableRows">
					{{ savingAction === "freeze-static" ? "正在冻结..." : "冻结静态表" }}
				</button>
				<button type="button" :disabled="saving || !staticTablePayload?.frozen" @click="unfreezeStaticTableRows">
					{{ savingAction === "unfreeze-static" ? "正在解冻..." : "解冻静态表" }}
				</button>
			</div>

			<div v-if="!staticTableDraftRows.length" class="empty-state">当前材料尚未生成 ChatGPT 静态三栏表。请点击“生成 ChatGPT 三栏表”。</div>
			<div v-else class="gpt-table-output" aria-label="ChatGPT 静态三栏表预览与编辑">
				<table class="gpt-markdown-table" :class="{ editable: !staticTablePayload?.frozen }">
					<thead>
						<tr>
							<th>左侧</th>
							<th>比较项</th>
							<th>右侧</th>
							<th v-if="!staticTablePayload?.frozen" class="row-actions">操作</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(row, index) in staticTableDraftRows" :key="row.draft_id || row.id || index">
							<td v-if="staticTablePayload?.frozen">{{ sideValue(row, "left") }}</td>
							<td v-else><textarea v-model="row.left.value" rows="3" :disabled="saving" aria-label="左侧内容"></textarea></td>
							<td v-if="staticTablePayload?.frozen" class="comparison-label">{{ row.label || `比较项 ${index + 1}` }}</td>
							<td v-else><input v-model="row.label" :disabled="saving" aria-label="比较项" /></td>
							<td v-if="staticTablePayload?.frozen">{{ sideValue(row, "right") }}</td>
							<td v-else><textarea v-model="row.right.value" rows="3" :disabled="saving" aria-label="右侧内容"></textarea></td>
							<td v-if="!staticTablePayload?.frozen" class="row-actions">
								<button type="button" :disabled="saving || staticTableDraftRows.length <= 1" @click="removeStaticTableRow(index)">删除</button>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</section>
	</section>
</template>

<script setup>
	import { computed, ref, watch } from "vue";
	import {
		adminFreezeQuestions,
		adminFreezeStaticTable,
		adminGenerateQuestions,
		adminGenerateStaticTable,
		adminQuestions,
		adminSaveStaticTable,
		adminStaticTable,
		adminUnfreezeQuestions,
		adminUnfreezeStaticTable
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
	const staticTablePayload = ref(null);
	const staticTableDraftRows = ref([]);
	const editingQuestions = ref({});
	const loading = ref(false);
	const savingAction = ref("");
	const message = ref("");
	const errorMessage = ref("");

	const saving = computed(() => Boolean(savingAction.value));
	const questions = computed(() => questionPayload.value?.questions || []);
	const questionsFrozen = computed(() => questionPayload.value?.frozen === true);
	const promptInfo = computed(() => questionPayload.value?.generation_prompts || null);
	const staticTablePromptInfo = computed(() => staticTablePayload.value?.generation_prompts || null);

	const showError = error => {
		errorMessage.value = error.response?.data?.error || error.message || "操作失败，请稍后重试。";
	};

	const syncStaticTableEditor = () => {
		staticTableDraftRows.value = (staticTablePayload.value?.rows || []).map(toStaticTableRowDraft);
	};

	const loadQuestions = async () => {
		loading.value = true;
		message.value = "";
		errorMessage.value = "";
		editingQuestions.value = {};
		try {
			const [questionsResponse, staticResponse] = await Promise.all([
				adminQuestions(props.token, selectedMaterial.value),
				adminStaticTable(props.token, selectedMaterial.value)
			]);
			questionPayload.value = questionsResponse;
			staticTablePayload.value = staticResponse;
			syncStaticTableEditor();
		} catch (error) {
			questionPayload.value = null;
			staticTablePayload.value = null;
			showError(error);
		} finally {
			loading.value = false;
		}
	};

	watch(selectedMaterial, loadQuestions, { immediate: true });

	const autoGenerateQuestions = async () => {
		if (questionsFrozen.value) return;
		savingAction.value = "auto-generate";
		message.value = "";
		errorMessage.value = "";
		try {
			questionPayload.value = await adminGenerateQuestions(props.token, selectedMaterial.value);
			editingQuestions.value = {};
			message.value = "题目已由系统自动生成并保存为未冻结版本，请检查题目、隐藏标准答案和 prompt 后冻结。";
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
			editingQuestions.value = {};
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

	const startEditQuestion = question => {
		if (questionsFrozen.value) return;
		editingQuestions.value = {
			...editingQuestions.value,
			[question.question_id]: toQuestionDraft(question)
		};
	};

	const cancelEditQuestion = questionId => {
		const next = { ...editingQuestions.value };
		delete next[questionId];
		editingQuestions.value = next;
	};

	const addGoldAtom = questionId => {
		const draft = editingQuestions.value[questionId];
		if (!draft) return;
		draft.gold_atoms.push(emptyGoldAtomDraft(questionId, draft.gold_atoms.length));
	};

	const removeGoldAtom = (questionId, atomIndex) => {
		const draft = editingQuestions.value[questionId];
		if (!draft || draft.gold_atoms.length <= 1) return;
		draft.gold_atoms.splice(atomIndex, 1);
	};

	const saveQuestionEdit = async question => {
		const draft = editingQuestions.value[question.question_id];
		if (!draft || questionsFrozen.value) return;
		savingAction.value = `save-question-${question.question_id}`;
		message.value = "";
		errorMessage.value = "";
		try {
			const nextQuestions = questions.value.map(item => item.question_id === question.question_id ? fromQuestionDraft(item, draft) : item);
			questionPayload.value = await adminGenerateQuestions(props.token, selectedMaterial.value, {
				...questionPayload.value,
				questions: nextQuestions
			});
			cancelEditQuestion(question.question_id);
			message.value = `${question.question_id} 已保存。`;
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const generateStaticTableRows = async () => {
		if (staticTablePayload.value?.frozen) return;
		savingAction.value = "generate-static";
		message.value = "";
		errorMessage.value = "";
		try {
			staticTablePayload.value = await adminGenerateStaticTable(props.token, selectedMaterial.value);
			syncStaticTableEditor();
			message.value = "ChatGPT 静态三栏表已生成，请检查真实表格内容后冻结。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const saveStaticTableRows = async () => {
		if (!staticTableDraftRows.value.length || staticTablePayload.value?.frozen) return;
		savingAction.value = "save-static";
		message.value = "";
		errorMessage.value = "";
		try {
			const rows = staticTableDraftRows.value.map(fromStaticTableRowDraft);
			staticTablePayload.value = await adminSaveStaticTable(props.token, selectedMaterial.value, rows);
			syncStaticTableEditor();
			message.value = "静态三栏表修改已保存。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const addStaticTableRow = () => {
		staticTableDraftRows.value.push(emptyStaticTableRowDraft(staticTableDraftRows.value.length));
	};

	const removeStaticTableRow = index => {
		if (staticTableDraftRows.value.length <= 1) return;
		staticTableDraftRows.value.splice(index, 1);
	};

	const freezeStaticTableRows = async () => {
		savingAction.value = "freeze-static";
		message.value = "";
		errorMessage.value = "";
		try {
			staticTablePayload.value = await adminFreezeStaticTable(props.token, selectedMaterial.value);
			syncStaticTableEditor();
			message.value = "静态表已冻结。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const unfreezeStaticTableRows = async () => {
		savingAction.value = "unfreeze-static";
		message.value = "";
		errorMessage.value = "";
		try {
			staticTablePayload.value = await adminUnfreezeStaticTable(props.token, selectedMaterial.value);
			syncStaticTableEditor();
			message.value = "静态表已解冻。";
		} catch (error) {
			showError(error);
		} finally {
			savingAction.value = "";
		}
	};

	const goldAtoms = question => question.gold_atoms || [];

	const toQuestionDraft = question => ({
		question_type: question.question_type || "",
		question_text: question.question_text || "",
		answer_format: question.answer_format || "",
		understanding_target: question.understanding_target || "",
		answer_options_text: (question.answer_options || []).join("\n"),
		gold_atoms: (question.gold_atoms?.length ? question.gold_atoms : [emptyGoldAtomDraft(question.question_id, 0)]).map((atom, index) => ({
			...atom,
			draft_id: `${question.question_id}-draft-${index}-${Date.now()}`,
			atom_id: atom.atom_id || `${question.question_id}-A${index + 1}`,
			requirement: atom.requirement || "",
			canonical_answer: atom.canonical_answer || "",
			accepted_variants_text: (atom.accepted_variants || []).join("\n"),
			source_ids_text: (atom.source_ids || []).join("\n"),
			required_unit: atom.required_unit || "",
			required_time_scope: atom.required_time_scope || ""
		}))
	});

	const fromQuestionDraft = (original, draft) => ({
		...original,
		question_type: draft.question_type,
		question_text: draft.question_text,
		answer_format: draft.answer_format,
		understanding_target: draft.understanding_target,
		answer_options: splitList(draft.answer_options_text),
		gold_atoms: draft.gold_atoms.map((atom, index) => {
			const { draft_id: draftId, accepted_variants_text: acceptedVariantsText, source_ids_text: sourceIdsText, ...rest } = atom;
			void draftId;
			return {
				...rest,
				atom_id: rest.atom_id || `${original.question_id}-A${index + 1}`,
				accepted_variants: splitList(acceptedVariantsText),
				source_ids: splitList(sourceIdsText)
			};
		})
	});

	const toStaticTableRowDraft = (row, index) => ({
		...row,
		draft_id: `${row.id || "row"}-${index}-${Date.now()}`,
		id: row.id || `R${index + 1}`,
		label: row.label || "",
		left: { value: sideValue(row, "left") === "—" ? "" : sideValue(row, "left") },
		right: { value: sideValue(row, "right") === "—" ? "" : sideValue(row, "right") }
	});

	const fromStaticTableRowDraft = (row, index) => ({
		id: row.id || `R${index + 1}`,
		label: row.label || `比较项 ${index + 1}`,
		left: { value: row.left?.value || "材料未明确说明" },
		right: { value: row.right?.value || "材料未明确说明" }
	});

	const emptyStaticTableRowDraft = index => ({
		draft_id: `static-row-${index}-${Date.now()}`,
		id: `R${index + 1}`,
		label: "",
		left: { value: "" },
		right: { value: "" }
	});

	const stringifyValue = value => {
		if (value === null || value === undefined || value === "") return "—";
		if (["string", "number", "boolean"].includes(typeof value)) return String(value);
		if (Array.isArray(value)) return value.map(stringifyValue).join("; ");
		if (value.display || value.rawText || value.raw || value.value) return stringifyValue(value.display || value.rawText || value.raw || value.value);
		return JSON.stringify(value);
	};

	const sideValue = (row, side) => {
		const sideData = row?.visualization?.[side] || row?.[side] || {};
		if (Array.isArray(sideData.values) && sideData.values.length) return sideData.values.map(value => stringifyValue(value)).join("; ");
		return stringifyValue(sideData.raw || sideData.value || sideData.text || row?.[`${side}Value`]);
	};

	function emptyGoldAtomDraft(questionId, index) {
		return {
			draft_id: `${questionId}-new-${index}-${Date.now()}`,
			atom_id: `${questionId}-A${index + 1}`,
			requirement: "",
			canonical_answer: "",
			accepted_variants_text: "",
			source_ids_text: "",
			required_unit: "",
			required_time_scope: ""
		};
	}

	function splitList(value) {
		return String(value || "")
			.split(/[\n,，]/)
			.map(item => item.trim())
			.filter(Boolean);
	}
</script>

<style scoped>
	.admin-panel { display: grid; gap: 20px; }
	.panel-header { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; }
	h2 { margin: 0 0 8px; font-size: 28px; color: #172033; }
	p { margin: 0; color: #64748b; }
	.material-select { display: grid; gap: 8px; min-width: 280px; font-weight: 800; color: #334155; }
	select, textarea, input { border: 1px solid #cbd5e1; border-radius: 12px; padding: 10px 12px; font: inherit; background: #ffffff; }
	textarea, input { width: 100%; box-sizing: border-box; }
	textarea { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; font-size: 13px; resize: vertical; }
	.status-card { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; border: 1px solid #dbe4ee; border-radius: 16px; padding: 16px; background: #f8fafc; }
	.status-card div { display: grid; gap: 4px; }
	.status-card strong { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }
	.status-card span { font-weight: 800; color: #172033; word-break: break-word; }
	.frozen { color: #b45309 !important; }
	.unfrozen { color: #047857 !important; }
	.questions-list { display: grid; gap: 14px; }
	.question-card, .question-actions-card, .prompt-card, .static-table-card, .empty-state, .loading-state, .notice { border: 1px solid #dbe4ee; border-radius: 16px; padding: 16px; background: #ffffff; }
	.question-actions-card, .prompt-card { display: grid; gap: 14px; }
	.question-card header, .question-actions-card { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
	.question-card header > div:first-child { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
	.card-actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
	.question-id, .question-type { border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 900; }
	.question-id { background: #dbeafe; color: #1d4ed8; }
	.question-type { background: #f1f5f9; color: #334155; }
	h3 { margin: 0 0 10px; font-size: 18px; line-height: 1.45; color: #172033; }
	.question-meta { display: grid; gap: 8px; margin: 0 0 14px; }
	.question-meta div { display: grid; gap: 4px; }
	dt { font-weight: 900; color: #334155; }
	dd { margin: 0; color: #475569; line-height: 1.6; }
	.gold-block, .static-table-card, .question-edit-form, .atom-editor, .prompt-grid { display: grid; gap: 12px; }
	.gold-block strong, .question-edit-form label, .atom-editor strong { font-weight: 900; color: #334155; }
	.question-edit-form label, .atom-edit-card label { display: grid; gap: 6px; }
	.atom-editor header, .atom-edit-header { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
	.gold-atom-list { display: grid; gap: 10px; }
	.gold-atom-card, .atom-edit-card, .prompt-note { border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px; background: #f8fafc; display: grid; gap: 8px; }
	.gold-atom-card p { color: #334155; }
	.atom-title { font-weight: 900; color: #1d4ed8; }
	.source-chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
	.source-chip { border-radius: 999px; padding: 3px 8px; background: #e0f2fe; color: #0369a1; font-size: 12px; font-weight: 900; }
	.empty-inline { color: #64748b; }
	.prompt-card summary { cursor: pointer; font-weight: 900; color: #334155; margin-bottom: 8px; }
	pre { max-height: 360px; overflow: auto; margin: 0; border-radius: 12px; padding: 12px; background: #0f172a; color: #e2e8f0; font-size: 12px; white-space: pre-wrap; }

	.static-table-card { display: grid; gap: 14px; }
	.gpt-table-output { overflow-x: auto; color: #0d0d0d; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 14px; line-height: 1.55; }
	.gpt-markdown-table { width: 100%; min-width: 760px; border-collapse: collapse; border-spacing: 0; font-size: 14px; line-height: 1.55; }
	.gpt-markdown-table th, .gpt-markdown-table td { border: 1px solid #d9d9e3; padding: 8px 12px; text-align: left; vertical-align: top; font-weight: 400; white-space: pre-wrap; overflow-wrap: anywhere; }
	.gpt-markdown-table th { background: #f7f7f8; color: #0d0d0d; font-weight: 600; }
	.gpt-markdown-table tbody tr:nth-child(even) td { background: #fcfcfd; }
	.gpt-markdown-table.editable td { padding: 0; background: #ffffff; }
	.gpt-markdown-table.editable td.row-actions { padding: 8px; width: 88px; text-align: center; }
	.gpt-markdown-table.editable textarea, .gpt-markdown-table.editable input { display: block; width: 100%; min-width: 180px; box-sizing: border-box; border: 0; border-radius: 0; padding: 8px 12px; background: transparent; color: #0d0d0d; font: inherit; line-height: 1.55; resize: vertical; outline: none; }
	.gpt-markdown-table.editable textarea { min-height: 82px; }
	.gpt-markdown-table.editable input { min-height: 40px; }
	.gpt-markdown-table.editable textarea:focus, .gpt-markdown-table.editable input:focus { box-shadow: inset 0 0 0 2px rgba(16, 163, 127, 0.35); background: #ffffff; }
	.comparison-label { font-weight: 400; color: #0d0d0d; }
	.action-row { display: flex; flex-wrap: wrap; gap: 10px; }
	button { border: 1px solid #cbd5e1; border-radius: 12px; padding: 10px 14px; background: #ffffff; color: #172033; font-weight: 900; cursor: pointer; }
	button.primary { border-color: #2563eb; background: #2563eb; color: #ffffff; }
	button:disabled { cursor: not-allowed; opacity: 0.55; }
	.notice.success { border-color: #bbf7d0; background: #f0fdf4; color: #166534; }
	.notice.error { border-color: #fecaca; background: #fff7f7; color: #991b1b; }
	.empty-state, .loading-state { color: #64748b; text-align: center; }
	@media (max-width: 760px) {
		.panel-header, .question-actions-card, .question-card header { display: grid; }
		.material-select { min-width: 0; }
		.card-actions { justify-content: flex-start; }
	}
</style>
