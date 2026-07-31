<template>
	<div class="loading-container">
		<div class="loading-spinner"></div>
		<div class="loading-text">{{ message }}</div>
	</div>
</template>

<script setup>
	const props = defineProps({
		message: {
			type: String,
			default: "Loading..."
		}
	});
</script>

<style scoped>
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 200px;
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #3498db;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loading-text {
		margin-top: 10px;
		font-size: 16px;
		color: #3498db;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
