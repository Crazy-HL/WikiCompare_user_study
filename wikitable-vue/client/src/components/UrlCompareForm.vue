<template>
	<form class="url-form" @submit.prevent="submit">
		<input v-model="leftUrl" placeholder="Left English Wikipedia URL" />
		<input v-model="rightUrl" placeholder="Right English Wikipedia URL" />
		<button type="submit" :disabled="store.isLoading">
			{{ store.isLoading ? "Loading..." : "Compare" }}
		</button>
		<p v-if="store.error" class="error">{{ store.error }}</p>
	</form>
</template>

<script setup>
	import { ref } from "vue";
	import { sessionStore as store } from "@/js/sessionStore";

	const leftUrl = ref("https://en.wikipedia.org/wiki/Economy_of_South_Korea");
	const rightUrl = ref("https://en.wikipedia.org/wiki/Economy_of_Japan");

	const submit = () => {
		store.loadSession(leftUrl.value, rightUrl.value);
	};
</script>

<style scoped>
	.url-form {
		display: grid;
		grid-template-columns: 1fr 1fr auto;
		gap: 8px;
		padding: 8px;
		background: #ffffff;
		border-bottom: 1px solid #e5e7eb;
	}

	input {
		min-width: 0;
		padding: 8px 10px;
		border: 1px solid #cbd5e1;
		border-radius: 6px;
	}

	button {
		padding: 8px 14px;
		border: 0;
		border-radius: 6px;
		background: #1f2937;
		color: white;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.65;
	}

	.error {
		grid-column: 1 / -1;
		margin: 0;
		color: #b91c1c;
		font-size: 13px;
	}

	@media (max-width: 760px) {
		.url-form {
			grid-template-columns: 1fr;
		}
	}
</style>
