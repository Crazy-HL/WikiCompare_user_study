<template>
	<header class="stage-header">
		<div>
			<p class="stage-kicker">第 {{ stageNumber }} / {{ stageCount }} 阶段</p>
			<h1>{{ materialLabel }}</h1>
		</div>
		<p class="instructions">
			请阅读两侧材料与中间信息，按题目填写你的答案、主要来源和证据位置。当前阶段由系统按你的实验编号自动加载。
		</p>
	</header>
</template>

<script setup>
	defineProps({
		stageNumber: {
			type: Number,
			required: true
		},
		stageCount: {
			type: Number,
			default: 2
		},
		materialLabel: {
			type: String,
			required: true
		}
	});
</script>

<style scoped>
	.stage-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 24px;
		padding: 18px 22px;
		border-bottom: 1px solid rgba(203, 213, 225, 0.9);
		background: rgba(255, 255, 255, 0.94);
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
	}

	.stage-kicker {
		margin: 0 0 4px;
		color: #2563eb;
		font-size: 13px;
		font-weight: 800;
	}

	h1 {
		margin: 0;
		font-size: 22px;
		line-height: 1.25;
		color: #172033;
	}

	.instructions {
		max-width: 680px;
		margin: 0;
		color: #475569;
		font-size: 14px;
		line-height: 1.55;
	}

	@media (max-width: 860px) {
		.stage-header {
			align-items: flex-start;
			flex-direction: column;
			gap: 10px;
		}
	}
</style>
