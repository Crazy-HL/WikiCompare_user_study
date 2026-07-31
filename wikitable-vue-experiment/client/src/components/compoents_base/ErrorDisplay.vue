<template>
	<div class="error-container">
		<div class="error-icon">⚠️</div>
		<div class="error-message">{{ message }}</div>
		<button class="retry-button" @click="onRetry">重试</button>
	</div>
</template>

<script setup>
	const props = defineProps({
		message: {
			type: String,
			required: true
		}
	});

	const emit = defineEmits(["retry"]);

	const onRetry = () => {
		emit("retry");
	};
</script>

<style scoped>
	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 20px;
		background-color: #fff3f3;
		border: 1px solid #ffcccc;
		border-radius: 8px;
		animation: fadeIn 0.5s ease;
	}

	.error-icon {
		font-size: 48px;
		color: #ff6b6b;
		margin-bottom: 10px;
	}

	.error-message {
		font-size: 16px;
		color: #ff6b6b;
		text-align: center;
		margin-bottom: 20px;
	}

	.retry-button {
		padding: 10px 20px;
		background-color: #ff6b6b;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		transition: background-color 0.3s ease;
	}

	.retry-button:hover {
		background-color: #ff4c4c;
	}

	.retry-button:active {
		background-color: #ff3333;
	}

	@keyframes fadeIn {
		0% {
			opacity: 0;
			transform: translateY(-10px);
		}
		100% {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
