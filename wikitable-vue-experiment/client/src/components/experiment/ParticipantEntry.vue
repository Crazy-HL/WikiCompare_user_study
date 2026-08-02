<template>
	<section class="participant-entry">
		<div class="entry-card">
			<p class="eyebrow">WikiCompare 参与者实验</p>
			<h1>请选择你的实验编号</h1>
			<p class="instructions">
				请按照研究人员分配给你的实验编号选择对应项目。系统会自动加载指定材料和实验顺序；无需也不能选择条件。
			</p>

			<label class="code-field" for="participant-code">
				<span>实验编号</span>
				<select id="participant-code" v-model="selectedCode">
					<option v-for="code in participantCodes" :key="code" :value="code">
						{{ code }}
					</option>
				</select>
			</label>

			<button class="start-button" type="button" @click="emitStart">
				开始实验
			</button>
		</div>
	</section>
</template>

<script setup>
	import { ref } from "vue";

	const emit = defineEmits(["start"]);
	const participantCodes = Array.from({ length: 12 }, (_item, index) => `P${String(index + 1).padStart(2, "0")}`);
	const selectedCode = ref(participantCodes[0]);

	const emitStart = () => {
		emit("start", selectedCode.value);
	};
</script>

<style scoped>
	.participant-entry {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 32px 18px;
		box-sizing: border-box;
		background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 48%, #eef2ff 100%);
		color: #172033;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	.entry-card {
		width: min(520px, 100%);
		padding: 34px;
		border: 1px solid rgba(148, 163, 184, 0.34);
		border-radius: 22px;
		background: rgba(255, 255, 255, 0.92);
		box-shadow: 0 24px 70px rgba(30, 41, 59, 0.14);
	}

	.eyebrow {
		margin: 0 0 8px;
		color: #2563eb;
		font-weight: 780;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		font-size: 12px;
	}

	h1 {
		margin: 0;
		font-size: clamp(28px, 4vw, 38px);
		line-height: 1.12;
	}

	.instructions {
		margin: 16px 0 24px;
		color: #475569;
		font-size: 16px;
		line-height: 1.7;
	}

	.code-field {
		display: grid;
		gap: 8px;
		margin-bottom: 22px;
		font-weight: 700;
		color: #334155;
	}

	select {
		width: 100%;
		padding: 13px 14px;
		border: 1px solid #cbd5e1;
		border-radius: 12px;
		background: #ffffff;
		color: #0f172a;
		font-size: 18px;
		font-weight: 740;
	}

	.start-button {
		width: 100%;
		border: 0;
		border-radius: 12px;
		padding: 14px 18px;
		background: #2563eb;
		color: #ffffff;
		font-size: 17px;
		font-weight: 800;
		cursor: pointer;
		box-shadow: 0 10px 22px rgba(37, 99, 235, 0.24);
	}

	.start-button:hover {
		background: #1d4ed8;
	}
</style>
