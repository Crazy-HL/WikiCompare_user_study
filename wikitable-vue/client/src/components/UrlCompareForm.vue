<template>
	<section class="url-shell" :class="{ expanded: isExpanded }">
		<div class="url-summary">
			<div class="summary-text">
				<strong>WikiCompare</strong>
				<span>{{ summaryText }}</span>
			</div>
			<button class="toggle-button" type="button" @click="toggleExpanded">
				{{ isExpanded ? "Hide" : "Change URLs" }}
			</button>
		</div>

		<form v-if="isExpanded" class="url-form" @submit.prevent="submit">
			<label>
				<span>Left article</span>
				<input v-model="leftUrl" placeholder="English Wikipedia URL" />
			</label>
			<label>
				<span>Right article</span>
				<input v-model="rightUrl" placeholder="English Wikipedia URL" />
			</label>
			<button class="submit-button" type="submit" :disabled="store.isLoading">
				{{ store.isLoading ? "Loading..." : "Compare" }}
			</button>
			<p v-if="store.error" class="error">{{ store.error }}</p>
		</form>
	</section>
</template>

<script setup>
	import { computed, ref, watch } from "vue";
	import { sessionStore as store } from "@/js/sessionStore";

	const leftUrl = ref("https://en.wikipedia.org/wiki/Economy_of_South_Korea");
	const rightUrl = ref("https://en.wikipedia.org/wiki/Economy_of_Japan");
	const isExpanded = ref(!store.session);

	const summaryText = computed(() => {
		const leftTitle = store.session?.articles?.left?.title;
		const rightTitle = store.session?.articles?.right?.title;
		if (store.isLoading) return "Loading Wikipedia articles...";
		if (leftTitle && rightTitle) return `${leftTitle} vs ${rightTitle}`;
		return "Ready to compare two English Wikipedia articles";
	});

	const submit = () => {
		store.loadSession(leftUrl.value, rightUrl.value);
	};

	const toggleExpanded = () => {
		isExpanded.value = !isExpanded.value;
	};

	watch(
		() => [store.session, store.error],
		([session, error]) => {
			if (error) isExpanded.value = true;
			if (session && !error) isExpanded.value = false;
		}
	);
</script>

<style scoped>
	.url-shell {
		position: relative;
		z-index: 20;
		background: rgba(255, 255, 255, 0.94);
		border-bottom: 1px solid rgba(190, 201, 216, 0.86);
		box-shadow:
			0 1px 2px rgba(15, 23, 42, 0.04),
			0 8px 20px rgba(15, 23, 42, 0.05);
		backdrop-filter: blur(12px);
	}

	.url-summary {
		display: flex;
		min-height: 46px;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 7px 14px;
	}

	.summary-text {
		display: flex;
		min-width: 0;
		align-items: baseline;
		gap: 12px;
		color: #334155;
		font-size: 12px;
		letter-spacing: 0;
	}

	.summary-text strong {
		color: #0f172a;
		font-size: 15px;
		font-weight: 750;
	}

	.summary-text span {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: #64748b;
	}

	.url-form {
		display: grid;
		grid-template-columns: 1fr 1fr auto;
		gap: 12px;
		padding: 2px 14px 14px;
		align-items: end;
	}

	label {
		display: grid;
		gap: 5px;
		min-width: 0;
		color: #475569;
		font-size: 11px;
		font-weight: 650;
	}

	input {
		min-width: 0;
		padding: 9px 11px;
		border: 1px solid #c7d2e2;
		border-radius: 7px;
		background: #fbfdff;
		color: #0f172a;
		font-size: 13px;
		transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
	}

	input:focus {
		outline: none;
		border-color: #3867a8;
		background: #ffffff;
		box-shadow: 0 0 0 3px rgba(56, 103, 168, 0.16);
	}

	button {
		min-height: 34px;
		padding: 7px 13px;
		border: 1px solid #cbd5e1;
		border-radius: 7px;
		background: #ffffff;
		color: #243447;
		cursor: pointer;
		font-size: 12px;
		font-weight: 650;
		transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease, background 0.16s ease;
	}

	button:hover:not(:disabled) {
		border-color: #9fb0c4;
		background: #f8fafc;
		box-shadow: 0 2px 7px rgba(15, 23, 42, 0.08);
		transform: translateY(-1px);
	}

	.submit-button {
		border-color: #243447;
		background: #243447;
		color: white;
	}

	.submit-button:hover:not(:disabled) {
		border-color: #1b2a3a;
		background: #1b2a3a;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.65;
	}

	.error {
		grid-column: 1 / -1;
		margin: 0;
		color: #b91c1c;
		font-size: 12px;
	}

	@media (max-width: 760px) {
		.url-form {
			grid-template-columns: 1fr;
		}
	}
</style>
