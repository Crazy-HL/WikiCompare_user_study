<template>
	<section class="url-shell" :class="{ expanded: isExpanded }">
		<div class="url-summary">
			<div class="summary-text">
				<strong>WikiCompare</strong>
				<span class="summary-status">{{ summaryText }}</span>
			</div>
			<button class="toggle-button" type="button" @click="toggleExpanded">
				{{ isExpanded ? "Collapse" : "Change" }}
			</button>
		</div>

		<form v-if="isExpanded" class="url-form" @submit.prevent="submit">
			<div class="material-panel">
				<div class="material-header">
					<span>Experiment materials</span>
					<small>Click a pair to load fixed-version or official web materials</small>
				</div>
				<div class="material-list">
					<button
						v-for="preset in MATERIAL_PRESETS"
						:key="preset.id"
						class="material-card"
						type="button"
						:disabled="store.isLoading"
						@click="selectMaterial(preset)">
						<strong>{{ preset.label }}</strong>
						<span>{{ preset.type }}</span>
						<small>{{ preset.description }}</small>
					</button>
				</div>
			</div>
			<label>
				<span>Left article</span>
				<textarea
					v-model="leftUrl"
					rows="3"
					placeholder="Article URL or pasted article text"></textarea>
			</label>
			<label>
				<span>Right article</span>
				<textarea
					v-model="rightUrl"
					rows="3"
					placeholder="Article URL or pasted article text"></textarea>
			</label>
			<div class="form-actions">
				<button class="submit-button" type="submit" :disabled="store.isLoading">
					{{ store.isLoading ? "Loading..." : "Compare" }}
				</button>
				<button class="refresh-button" type="button" :disabled="store.isLoading || !store.session" @click="regenerate">
					Regenerate
				</button>
			</div>
			<p v-if="offlineStatusText" class="offline-note">{{ offlineStatusText }}</p>
			<p v-if="store.error" class="error">{{ store.error }}</p>
			<div v-if="historyItems.length" class="history-panel">
				<div class="history-title">Recent comparisons</div>
				<div class="history-list">
					<div
						v-for="item in historyItems"
						:key="item.key"
						class="history-item"
						:class="{ active: item.key === store.activeHistoryKey }">
						<button
							class="history-select"
							type="button"
							@click="selectHistory(item.key)">
							<span>{{ item.leftTitle }}</span>
							<strong>vs</strong>
							<span>{{ item.rightTitle }}</span>
						</button>
						<button
							class="history-delete"
							type="button"
							title="Delete this comparison"
							aria-label="Delete this comparison"
							@click.stop="deleteHistory(item.key)">
							×
						</button>
					</div>
				</div>
			</div>
		</form>
	</section>
</template>

<script setup>
	import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
	import { sessionStore as store } from "@/js/sessionStore";
	const {
		isOfflineNow,
		WIKICOMPARE_OFFLINE_MESSAGE,
	} = require("@/js/offlineSupport");
	const { MATERIAL_PRESETS, materialUrl } = require("@/js/materialPresets");

	const EXAMPLE_CANONICAL_URLS = {
		left: "https://en.wikipedia.org/wiki/Economy_of_South_Korea",
		right: "https://en.wikipedia.org/wiki/Economy_of_Japan"
	};
	const EXAMPLE_URLS = {
		left: "https://en.wikipedia.org/w/index.php?title=Economy_of_South_Korea&oldid=1273871505",
		right: "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898"
	};
	const fixedExampleUrl = (side, url) =>
		String(url || "").replace(/\/+$/, "") === EXAMPLE_CANONICAL_URLS[side]
			? EXAMPLE_URLS[side]
			: url;
	const normalizeComparableUrl = url => String(url || "").trim().replace(/\/+$/, "");
	const presetForUrls = (left, right) =>
		MATERIAL_PRESETS.find(preset =>
			normalizeComparableUrl(materialUrl(preset.left)) === normalizeComparableUrl(fixedExampleUrl("left", left)) &&
			normalizeComparableUrl(materialUrl(preset.right)) === normalizeComparableUrl(fixedExampleUrl("right", right))
		);
	const loadOptionsForUrls = (left, right, baseOptions = {}) => {
		const preset = presetForUrls(left, right);
		if (!preset) return baseOptions;
		return {
			...baseOptions,
			leftTitle: preset.left.title,
			rightTitle: preset.right.title
		};
	};
	const initialUrlForSide = side =>
		fixedExampleUrl(side, store.session?.articles?.[side]?.url) ||
		fixedExampleUrl(side, store.history?.[0]?.[`${side}Url`]) ||
		EXAMPLE_URLS[side];

	const leftUrl = ref(initialUrlForSide("left"));
	const rightUrl = ref(initialUrlForSide("right"));
	const isExpanded = ref(!store.session);
	const isOffline = ref(isOfflineNow());
	const historyItems = computed(() => store.history || []);
	const buildLoadRequest = baseOptions => loadOptionsForUrls(
		leftUrl.value,
		rightUrl.value,
		baseOptions
	);

	const summaryText = computed(() => {
		const leftTitle = store.session?.articles?.left?.title;
		const rightTitle = store.session?.articles?.right?.title;
		if (isOffline.value && leftTitle && rightTitle) return `${leftTitle} vs ${rightTitle} (offline cache)`;
		if (store.isLoading) return "Loading source pages...";
		if (leftTitle && rightTitle) return `${leftTitle} vs ${rightTitle}`;
		return "Ready to compare two source pages";
	});

	const offlineStatusText = computed(() =>
		isOffline.value
			? `${WIKICOMPARE_OFFLINE_MESSAGE} 当前离线，Compare/Regenerate 需要联网。`
			: ""
	);

	const updateOfflineState = () => {
		isOffline.value = isOfflineNow();
		if (isOffline.value) {
			store.error = WIKICOMPARE_OFFLINE_MESSAGE;
		}
	};

	onMounted(() => {
		window.addEventListener("offline", updateOfflineState);
		window.addEventListener("online", updateOfflineState);
		updateOfflineState();
	});

	onBeforeUnmount(() => {
		window.removeEventListener("offline", updateOfflineState);
		window.removeEventListener("online", updateOfflineState);
	});

	const submit = () => {
		store.loadSession(
			leftUrl.value,
			rightUrl.value,
			buildLoadRequest()
		);
	};

	const regenerate = () => {
		store.loadSession(
			leftUrl.value,
			rightUrl.value,
			buildLoadRequest({ forceRefresh: true })
		);
	};

	const selectMaterial = preset => {
		const left = materialUrl(preset.left);
		const right = materialUrl(preset.right);
		leftUrl.value = left;
		rightUrl.value = right;
		store.loadSession(left, right, {
			forceRefresh: true,
			leftTitle: preset.left.title,
			rightTitle: preset.right.title
		});
	};

	const selectHistory = itemKey => {
		store.selectHistory(itemKey);
	};

	const deleteHistory = itemKey => {
		store.removeHistory(itemKey);
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

	watch(
		() => store.session,
		session => {
			const left = session?.articles?.left?.inputContent || session?.articles?.left?.url;
			const right = session?.articles?.right?.inputContent || session?.articles?.right?.url;
			if (left) leftUrl.value = left;
			if (right) rightUrl.value = right;
		}
	);
</script>

<style scoped>
	.url-shell {
		position: fixed;
		top: 10px;
		right: 12px;
		z-index: 1000;
		width: auto;
		background: transparent;
		border: 0;
		box-shadow: none;
		backdrop-filter: none;
	}

	.url-shell.expanded {
		left: 50%;
		right: auto;
		width: min(980px, calc(100vw - 24px));
		max-height: calc(100vh - 24px);
		overflow: auto;
		transform: translateX(-50%);
		background: rgba(252, 253, 255, 0.98);
		border: 1px solid rgba(205, 214, 226, 0.9);
		border-radius: 10px;
		box-shadow:
			0 18px 44px rgba(15, 23, 42, 0.18),
			0 1px 0 rgba(255, 255, 255, 0.8) inset;
		backdrop-filter: blur(10px);
	}

	.url-summary {
		display: flex;
		min-height: 42px;
		align-items: center;
		justify-content: space-between;
		gap: 14px;
		padding: 6px 18px;
	}

	.url-shell:not(.expanded) .url-summary {
		min-height: 0;
		padding: 10px 8px;
		opacity: 0;
		pointer-events: none;
		transform: translateY(-5px);
		transition: opacity 0.16s ease, transform 0.16s ease;
	}

	.url-shell:not(.expanded) {
		width: 96px;
		height: 52px;
	}

	.url-shell:not(.expanded):hover .url-summary,
	.url-shell:not(.expanded):focus-within .url-summary {
		opacity: 1;
		pointer-events: auto;
		transform: translateY(0);
	}

	.url-shell:not(.expanded) .summary-text {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		clip-path: inset(50%);
		white-space: nowrap;
	}

	.summary-text {
		display: flex;
		min-width: 0;
		align-items: baseline;
		gap: 10px;
		color: #334155;
		font-size: 12px;
		letter-spacing: 0;
	}

	.summary-text strong {
		color: #0f172a;
		font-size: 15px;
		font-weight: 800;
	}

	.summary-status {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: #667085;
		font-weight: 650;
	}

	.url-form {
		display: grid;
		grid-template-columns: 1fr 1fr auto;
		gap: 12px;
		padding: 8px 18px 16px;
		align-items: end;
		background: linear-gradient(180deg, rgba(248, 250, 252, 0.74), rgba(255, 255, 255, 0.96));
		border-top: 1px solid rgba(226, 232, 240, 0.8);
	}

	.material-panel {
		grid-column: 1 / -1;
		display: grid;
		gap: 8px;
	}

	.material-header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		color: #344054;
	}

	.material-header span {
		font-size: 12px;
		font-weight: 800;
	}

	.material-header small {
		color: #667085;
		font-size: 11px;
		font-weight: 600;
	}

	.material-list {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 8px;
	}

	.material-card {
		display: grid;
		min-height: 86px;
		align-content: start;
		gap: 5px;
		padding: 10px;
		text-align: left;
		border-color: #d8e1ec;
		background: #ffffff;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
	}

	.material-card strong {
		color: #172033;
		font-size: 12px;
		line-height: 1.25;
	}

	.material-card span {
		color: #3867a8;
		font-size: 11px;
		font-weight: 750;
	}

	.material-card small {
		color: #667085;
		font-size: 11px;
		line-height: 1.35;
	}

	.form-actions {
		display: flex;
		gap: 8px;
		align-items: end;
	}

	label {
		display: grid;
		gap: 6px;
		min-width: 0;
		color: #5b6778;
		font-size: 11px;
		font-weight: 760;
	}

	input,
	textarea {
		min-width: 0;
		min-height: 36px;
		padding: 8px 11px;
		border: 1px solid #cbd6e3;
		border-radius: 6px;
		background: #ffffff;
		color: #0f172a;
		font-size: 13px;
		font-family: inherit;
		transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
	}

	textarea {
		height: 62px;
		line-height: 1.35;
		resize: vertical;
	}

	input:focus,
	textarea:focus {
		outline: none;
		border-color: #3867a8;
		background: #ffffff;
		box-shadow: 0 0 0 3px rgba(56, 103, 168, 0.16);
	}

	button {
		min-height: 34px;
		padding: 7px 12px;
		border: 1px solid #cbd5e1;
		border-radius: 6px;
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

	.refresh-button {
		background: #f7fafc;
		color: #334155;
	}

	.toggle-button {
		flex: 0 0 auto;
		min-width: 78px;
		min-height: 32px;
		border-color: #d6dee9;
		background: #ffffff;
		color: #344054;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
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

	.offline-note {
		grid-column: 1 / -1;
		margin: 0;
		color: #8a5a00;
		font-size: 12px;
		font-weight: 650;
	}

	.history-panel {
		grid-column: 1 / -1;
		display: grid;
		gap: 8px;
		padding-top: 4px;
	}

	.history-title {
		color: #64748b;
		font-size: 11px;
		font-weight: 700;
	}

	.history-list {
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
	}

	.history-item {
		display: inline-flex;
		min-height: 28px;
		max-width: 360px;
		align-items: center;
		gap: 2px;
		padding: 0;
		border-color: #d8e1ec;
		background: #ffffff;
		color: #475569;
	}

	.history-select {
		display: inline-flex;
		min-width: 0;
		min-height: 28px;
		align-items: center;
		gap: 6px;
		padding: 5px 7px 5px 9px;
		border: 0;
		background: transparent;
		color: inherit;
		box-shadow: none;
	}

	.history-select:hover:not(:disabled) {
		border-color: transparent;
		background: transparent;
		box-shadow: none;
		transform: none;
	}

	.history-select span {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.history-select strong {
		color: #94a3b8;
		font-size: 10px;
		text-transform: uppercase;
	}

	.history-delete {
		display: inline-flex;
		width: 24px;
		min-width: 24px;
		min-height: 24px;
		height: 24px;
		align-items: center;
		justify-content: center;
		margin-right: 2px;
		padding: 0;
		border: 0;
		border-radius: 999px;
		background: transparent;
		color: #94a3b8;
		font-size: 16px;
		line-height: 1;
		box-shadow: none;
	}

	.history-delete:hover:not(:disabled) {
		background: #fee2e2;
		color: #b91c1c;
		box-shadow: none;
		transform: none;
	}

	.history-item.active {
		border-color: #3867a8;
		background: #eef5ff;
		color: #1e3a5f;
	}

	@media (max-width: 760px) {
		.url-summary {
			padding: 7px 12px;
		}

		.url-form {
			grid-template-columns: 1fr;
			padding: 10px 12px 14px;
		}

		.material-list {
			grid-template-columns: 1fr;
		}

		.summary-text {
			align-items: flex-start;
			flex-direction: column;
			gap: 2px;
		}
	}
</style>
