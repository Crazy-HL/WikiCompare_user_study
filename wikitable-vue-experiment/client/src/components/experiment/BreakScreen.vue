<template>
	<section class="break-screen">
		<div class="message-card">
			<h1>第一阶段已完成，请按研究人员要求休息后继续。</h1>
			<button type="button" @click="$emit('continue')">继续第二阶段</button>
		</div>
	</section>
</template>

<script setup>
	defineEmits(["continue"]);
</script>

<style scoped>
	.break-screen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
		box-sizing: border-box;
		background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 100%);
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	.message-card {
		max-width: 640px;
		padding: 36px;
		border-radius: 22px;
		background: #ffffff;
		border: 1px solid #bbf7d0;
		text-align: center;
		box-shadow: 0 22px 60px rgba(21, 128, 61, 0.14);
	}

	h1 {
		margin: 0 0 24px;
		color: #166534;
		font-size: clamp(24px, 3.4vw, 34px);
		line-height: 1.3;
	}

	button {
		border: 0;
		border-radius: 12px;
		padding: 13px 22px;
		background: #16a34a;
		color: #ffffff;
		font-size: 16px;
		font-weight: 820;
		cursor: pointer;
	}
</style>
