<template>
	<div :class="['div0', selectContentClass]" :id="divId" ref="divRef">
		<div v-if="!article" class="empty-state">
			<p>{{ store.isLoading ? "Loading article..." : "Enter two Wikipedia URLs to compare." }}</p>
		</div>
		<template v-else>
			<h1>{{ article.title }}</h1>
			<WikipediaContent :content="article.html" @select="handleSelection" />
			<ArticleOutline
				:outline="article.outline"
				:divId="divId"
				:matches="store.session?.outlineMatches || []" />
		</template>
	</div>
</template>

<script setup>
	import { computed, nextTick, onMounted, ref, watch } from "vue";
	import WikipediaContent from "./WikipediaContent.vue";
	import ArticleOutline from "./ArticleOutline.vue";
	import bus from "@/js/eventBus.js";
	import { sessionStore as store } from "@/js/sessionStore";

	const props = defineProps({
		side: String,
		divId: String,
		selectContentClass: String
	});

	const divRef = ref(null);
	const article = computed(() => store.session?.articles?.[props.side] || null);

	const cssEscape = value => {
		if (window.CSS?.escape) return window.CSS.escape(value);
		return String(value).replace(/"/g, '\\"');
	};

	const applyHighlights = () => {
		const root = divRef.value;
		if (!root) return;
		root.querySelectorAll(".source-highlight, .source-pinned").forEach(node => {
			node.classList.remove("source-highlight", "source-pinned");
		});
		store.highlightedSourceIds.forEach(id => {
			root.querySelectorAll(`[data-source-id="${cssEscape(id)}"]`).forEach(node => {
				node.classList.add("source-highlight");
			});
		});
		store.pinnedSourceIds.forEach(id => {
			root.querySelectorAll(`[data-source-id="${cssEscape(id)}"]`).forEach(node => {
				node.classList.add("source-pinned");
			});
		});
	};

	const findSourceNode = sourceIds => {
		const root = divRef.value;
		if (!root) return null;
		for (const id of sourceIds || []) {
			const node = root.querySelector(`[data-source-id="${cssEscape(id)}"]`);
			if (node) return node;
		}
		return null;
	};

	const revealHighlightedSource = () => {
		const node = findSourceNode(store.revealSourceIds);
		if (!node) return;
		node.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
	};

	const handleSelection = content => {
		bus.emit(`${props.divId}_Event`, { content });
	};

	watch(
		() => [store.highlightedSourceIds, store.pinnedSourceIds, article.value?.html],
		() => nextTick(applyHighlights),
		{ deep: true }
	);

	watch(
		() => store.revealRequestId,
		() => nextTick(revealHighlightedSource)
	);

	onMounted(() => {
		nextTick(applyHighlights);
	});
</script>

<style scoped>
	.div0 {
		position: relative;
		min-height: 100%;
		background: #ffffff;
	}

	h1 {
		margin: 14px 16px 6px;
		color: #172033;
		font-size: 20px;
		line-height: 1.25;
		font-weight: 760;
		letter-spacing: 0;
	}

	.empty-state {
		display: flex;
		min-height: 240px;
		align-items: center;
		justify-content: center;
		padding: 24px;
		color: #64748b;
		font-size: 13px;
		text-align: center;
	}

	:deep([data-source-id].source-highlight) {
		background: rgba(255, 228, 117, 0.52);
		outline: 2px solid rgba(217, 144, 47, 0.5);
		border-radius: 2px;
	}

	:deep([data-source-id].source-pinned) {
		background: rgba(56, 103, 168, 0.16);
		outline: 2px solid rgba(56, 103, 168, 0.52);
		border-radius: 2px;
	}

	:deep(.wikipedia-content) {
		font-size: 13px;
		line-height: 1.62;
		max-width: none;
	}

	:deep(table) {
		max-width: 100%;
		overflow-wrap: anywhere;
	}
</style>
