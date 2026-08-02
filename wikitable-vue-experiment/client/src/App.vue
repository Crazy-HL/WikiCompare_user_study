<template>
	<General v-if="routeMode === 'compare'" />
	<section v-else-if="routeMode === 'admin'" class="admin-placeholder">
		<div>
			<h1>管理后台</h1>
			<p>管理后台界面将在 Task 8 中实现。</p>
		</div>
	</section>
	<section v-else class="participant-app">
		<ParticipantEntry v-if="participantState === 'entry'" @start="beginExperiment" />
		<div v-else-if="participantState === 'starting'" class="app-message">正在加载实验配置...</div>
		<div v-else-if="participantState === 'error'" class="app-message error">
			<strong>无法开始实验</strong>
			<p>{{ errorMessage }}</p>
			<button type="button" @click="resetEntry">返回选择实验编号</button>
		</div>
		<ExperimentShell
			v-else-if="participantState === 'stage'"
			:assignment="assignment"
			:config="experimentConfig" />
	</section>
</template>

<script setup>
	import { computed, onMounted, onUnmounted, ref } from "vue";
	import General from "./components/general.vue";
	import ParticipantEntry from "./components/experiment/ParticipantEntry.vue";
	import ExperimentShell from "./components/experiment/ExperimentShell.vue";
	import { getExperimentConfig, startExperiment } from "@/experiment/experimentApi";
	const { assignmentForCode, validateAssignmentStages } = require("@/experiment/assignment");

	const currentPath = ref(window.location.pathname || "/");
	const participantState = ref("entry");
	const experimentConfig = ref(null);
	const assignment = ref(null);
	const errorMessage = ref("");

	const routeMode = computed(() => {
		if (currentPath.value.startsWith("/admin")) return "admin";
		if (currentPath.value.startsWith("/compare")) return "compare";
		return "participant";
	});

	const loadConfig = async () => {
		if (experimentConfig.value) return experimentConfig.value;
		experimentConfig.value = await getExperimentConfig();
		return experimentConfig.value;
	};

	const updateCurrentPath = () => {
		currentPath.value = window.location.pathname || "/";
	};

	onMounted(() => {
		window.addEventListener("popstate", updateCurrentPath);
		if (routeMode.value === "participant") {
			loadConfig().catch(error => {
				errorMessage.value = error.response?.data?.error || error.message || "实验配置加载失败。";
			});
		}
	});

	onUnmounted(() => {
		window.removeEventListener("popstate", updateCurrentPath);
	});

	const beginExperiment = async participantCode => {
		participantState.value = "starting";
		errorMessage.value = "";
		try {
			const localAssignment = assignmentForCode(participantCode);
			const [config, startedAssignment] = await Promise.all([
				loadConfig(),
				startExperiment(localAssignment.participantCode)
			]);
			experimentConfig.value = config;
			const mergedAssignment = {
				...localAssignment,
				...startedAssignment,
				group: startedAssignment.assignmentGroup || localAssignment.group,
				assignmentGroup: startedAssignment.assignmentGroup || localAssignment.group,
				stages: startedAssignment.stages || localAssignment.stages
			};
			const assignmentError = validateAssignmentStages(mergedAssignment);
			if (assignmentError) throw new Error(assignmentError);
			assignment.value = mergedAssignment;
			participantState.value = "stage";
		} catch (error) {
			errorMessage.value = error.response?.data?.error || error.message || "开始实验失败，请联系研究人员。";
			participantState.value = "error";
		}
	};

	const resetEntry = () => {
		participantState.value = "entry";
		errorMessage.value = "";
	};

</script>

<style scoped>
	.participant-app,
	.admin-placeholder,
	.app-message {
		min-height: 100vh;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	.admin-placeholder,
	.app-message {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
		box-sizing: border-box;
		background: #f8fafc;
		color: #172033;
		text-align: center;
	}

	.admin-placeholder > div,
	.app-message {
		max-width: 560px;
		border: 1px solid #dbe4ee;
		border-radius: 18px;
		padding: 30px;
		background: #ffffff;
		box-shadow: 0 18px 50px rgba(15, 23, 42, 0.1);
	}

	.admin-placeholder h1 {
		margin: 0 0 10px;
		font-size: 28px;
	}

	.admin-placeholder p,
	.app-message p {
		margin: 8px 0 0;
		color: #475569;
	}

	.app-message.error {
		color: #991b1b;
		background: #fff7f7;
		border-color: #fecaca;
	}

	.app-message button {
		margin-top: 16px;
		border: 0;
		border-radius: 10px;
		padding: 10px 14px;
		background: #2563eb;
		color: #ffffff;
		font-weight: 800;
		cursor: pointer;
	}
</style>
