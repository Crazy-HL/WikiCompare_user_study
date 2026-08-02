<template>
	<BreakScreen v-if="screen === 'break'" @continue="continueToNextStage" />
	<CompleteScreen v-else-if="screen === 'complete'" />

	<section v-else class="experiment-shell">
		<StageHeader
			:stage-number="currentStageDisplayIndex"
			:stage-count="stageCount"
			:material-label="currentMaterialLabel" />

		<div v-if="loadError" class="stage-error" role="alert">
			<strong>阶段加载失败</strong>
			<p>{{ loadError }}</p>
			<button type="button" @click="loadCurrentStage">重试</button>
		</div>

		<div v-else class="stage-layout">
			<div class="condition-column" :class="{ loading: isStageLoading }">
				<div v-if="isStageLoading" class="loading-overlay">
					正在加载当前材料与问题...
				</div>
				<General v-if="currentStage?.condition === 'wikicompare'" :key="`wiki-${currentStageKey}`" class="participant-general" />
				<ChatGptCondition v-else-if="currentStage?.condition === 'chatgpt'" :key="`chatgpt-${currentStageKey}`" />
			</div>

			<AnswerPanel
				:key="`answers-${currentStageKey}`"
				:questions="questions"
				:q6-text="q6Text"
				@submit="saveStageAnswers" />
		</div>
	</section>
</template>

<script setup>
	import { computed, ref, watch } from "vue";
	import General from "@/components/general.vue";
	import AnswerPanel from "./AnswerPanel.vue";
	import BreakScreen from "./BreakScreen.vue";
	import ChatGptCondition from "./ChatGptCondition.vue";
	import CompleteScreen from "./CompleteScreen.vue";
	import StageHeader from "./StageHeader.vue";
	import { getQuestions, completeExperiment } from "@/experiment/experimentApi";
	import { sessionStore } from "@/js/sessionStore";
	const { MATERIAL_PRESETS, materialUrl } = require("@/js/materialPresets");
	const { buildCompletionPayload } = require("@/experiment/experimentStore");
	const { Q6_TEXT } = require("@/experiment/q6");

	const props = defineProps({
		assignment: {
			type: Object,
			required: true
		},
		config: {
			type: Object,
			default: () => ({})
		}
	});

	const emit = defineEmits(["complete"]);
	const screen = ref("stage");
	const currentStageIndex = ref(0);
	const questionsPayload = ref(null);
	const isStageLoading = ref(false);
	const loadError = ref("");
	const stageStartedAtMs = ref(Date.now());
	const experimentStartedAtMs = Date.now();
	const stageResults = ref([]);

	const defaultMaterialPresetById = {
		M1: "economy-korea-japan",
		M2: "openfactbook-india-indonesia"
	};

	const stages = computed(() => props.assignment?.stages || []);
	const stageCount = computed(() => stages.value.length || 2);
	const currentStage = computed(() => stages.value[currentStageIndex.value] || null);
	const currentStageDisplayIndex = computed(() => currentStage.value?.stageIndex || currentStageIndex.value + 1);
	const currentStageKey = computed(() => `${currentStage.value?.stageIndex || currentStageIndex.value + 1}-${currentStage.value?.condition || ""}-${currentStage.value?.materialId || ""}`);
	const questions = computed(() => questionsPayload.value?.questions || []);
	const q6Text = computed(() => props.config?.q6Text || Q6_TEXT);
	const materials = computed(() => props.config?.materials || []);
	const currentMaterial = computed(() => materials.value.find(material => material.id === currentStage.value?.materialId) || null);
	const currentMaterialLabel = computed(() => currentMaterial.value?.label || currentStage.value?.materialId || "实验材料");
	const assignmentGroup = computed(() => props.assignment?.assignmentGroup || props.assignment?.group || "");

	const presetForMaterial = material => {
		const presetId = material?.presetId || material?.materialPresetId || material?.leftPresetId || defaultMaterialPresetById[material?.id];
		return MATERIAL_PRESETS.find(preset => preset.id === presetId) || null;
	};

	const loadCurrentMaterialSession = async stage => {
		const material = materials.value.find(item => item.id === stage.materialId) || { id: stage.materialId };
		const preset = presetForMaterial(material);
		if (!preset) {
			throw new Error(`未找到材料 ${stage.materialId} 对应的预设。`);
		}
		await sessionStore.loadSession(materialUrl(preset.left), materialUrl(preset.right), {
			leftTitle: material.leftTitle || preset.left.title,
			rightTitle: material.rightTitle || preset.right.title
		});
	};

	const loadCurrentStage = async () => {
		const stage = currentStage.value;
		if (!stage) {
			loadError.value = "未找到当前阶段。";
			return;
		}
		isStageLoading.value = true;
		loadError.value = "";
		questionsPayload.value = null;
		stageStartedAtMs.value = Date.now();
		try {
			const [payload] = await Promise.all([
				getQuestions(stage.materialId),
				loadCurrentMaterialSession(stage)
			]);
			questionsPayload.value = payload;
		} catch (error) {
			loadError.value = error.response?.data?.error || error.message || "加载阶段材料或问题时出错。";
		} finally {
			isStageLoading.value = false;
		}
	};

	watch(
		() => currentStageKey.value,
		() => {
			if (screen.value === "stage") loadCurrentStage();
		},
		{ immediate: true }
	);

	const saveStageAnswers = async answers => {
		const stage = currentStage.value;
		if (!stage) return;
		const stageSubmittedAtMs = Date.now();
		stageResults.value[currentStageIndex.value] = {
			stageIndex: stage.stageIndex,
			condition: stage.condition,
			materialId: stage.materialId,
			questionVersion: questionsPayload.value?.version || 0,
			stageStartedAtMs: stageStartedAtMs.value,
			stageSubmittedAtMs,
			answers
		};

		if (currentStageIndex.value < stageCount.value - 1) {
			screen.value = "break";
			return;
		}

		const completedAtMs = Date.now();
		const payload = buildCompletionPayload({
			experimentId: props.assignment?.experimentId,
			participantCode: props.assignment?.participantCode,
			assignmentGroup: assignmentGroup.value,
			startedAtMs: experimentStartedAtMs,
			completedAtMs,
			stages: stageResults.value.filter(Boolean)
		});
		try {
			const saved = await completeExperiment(payload);
			emit("complete", saved);
			screen.value = "complete";
		} catch (error) {
			loadError.value = error.response?.data?.error || error.message || "提交实验结果失败，请联系研究人员。";
		}
	};

	const continueToNextStage = () => {
		currentStageIndex.value += 1;
		screen.value = "stage";
		loadCurrentStage();
	};
</script>

<style scoped>
	.experiment-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		min-height: 0;
		background: #eef3f8;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	.stage-layout {
		display: flex;
		min-height: 0;
		flex: 1;
	}

	.condition-column {
		position: relative;
		flex: 1;
		min-width: 0;
		min-height: 0;
	}

	.condition-column.loading {
		pointer-events: none;
	}

	.loading-overlay {
		position: absolute;
		inset: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(248, 250, 252, 0.76);
		color: #334155;
		font-weight: 800;
		backdrop-filter: blur(2px);
	}

	.stage-error {
		margin: 16px;
		padding: 16px;
		border: 1px solid #fecaca;
		border-radius: 12px;
		background: #fef2f2;
		color: #991b1b;
	}

	.stage-error p {
		margin: 6px 0 12px;
	}

	.stage-error button {
		border: 0;
		border-radius: 8px;
		padding: 8px 12px;
		background: #dc2626;
		color: #ffffff;
		font-weight: 780;
		cursor: pointer;
	}

	.participant-general {
		height: 100%;
	}

	.participant-general :deep(.url-shell) {
		display: none;
	}

	.participant-general :deep(#root) {
		padding-top: 10px;
	}

	@media (max-width: 980px) {
		.experiment-shell {
			height: auto;
			min-height: 100vh;
		}

		.stage-layout {
			flex-direction: column;
		}

		.condition-column {
			min-height: 760px;
		}
	}
</style>
