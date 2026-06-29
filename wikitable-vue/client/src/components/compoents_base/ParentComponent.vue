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

	const handleSelection = content => {
		bus.emit(`${props.divId}_Event`, { content });
	};

	watch(
		() => [store.highlightedSourceIds, store.pinnedSourceIds, article.value?.html],
		() => nextTick(applyHighlights),
		{ deep: true }
	);

	onMounted(() => {
		nextTick(applyHighlights);
	});
</script>

<style scoped>
	.div0 {
		position: relative;
		min-height: 100%;
	}

	h1 {
		margin: 12px 14px 4px;
		font-size: 20px;
		line-height: 1.25;
	}

	.empty-state {
		display: flex;
		min-height: 240px;
		align-items: center;
		justify-content: center;
		padding: 24px;
		color: #64748b;
		text-align: center;
	}

	:deep([data-source-id].source-highlight) {
		background: rgba(253, 224, 71, 0.45);
		outline: 2px solid rgba(234, 179, 8, 0.55);
	}

	:deep([data-source-id].source-pinned) {
		background: rgba(96, 165, 250, 0.25);
		outline: 2px solid rgba(37, 99, 235, 0.6);
	}

	:deep(.wikipedia-content) {
		font-size: 13px;
		line-height: 1.55;
		max-width: none;
	}

	:deep(table) {
		max-width: 100%;
		overflow-wrap: anywhere;
	}
</style>
