<template>
	<div :class="['div0', selectContentClass]" :id="divId" ref="divRef">
		<div v-if="!article" class="empty-state">
			<p>{{ store.isLoading ? "Loading source page..." : "Enter two source page URLs to compare." }}</p>
		</div>
		<template v-else>
			<h1 class="article-title">{{ article.title }}</h1>
			<WikipediaContent
				:content="article.html"
				:sourceKind="article.sourceKind"
				@select="handleSelection" />
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
	const sourceNodeIndex = ref(new Map());
	const highlightClassByGroup = {
		relatedHighlighted: "source-related-highlight",
		highlighted: "source-highlight",
		pinned: "source-pinned",
		pinnedRelated: "source-related-pinned"
	};
	const appliedHighlightNodes = {
		relatedHighlighted: new Set(),
		highlighted: new Set(),
		pinned: new Set(),
		pinnedRelated: new Set()
	};

	const clearAppliedHighlightNodes = group => {
		const groups = group ? [group] : Object.keys(appliedHighlightNodes);
		groups.forEach(groupName => {
			const className = highlightClassByGroup[groupName];
			appliedHighlightNodes[groupName].forEach(node => {
				node.classList.remove(className);
			});
			appliedHighlightNodes[groupName].clear();
		});
	};

	const buildSourceNodeIndex = () => {
		const root = divRef.value;
		if (!root) return;
		const nextIndex = new Map();
		root.querySelectorAll("[data-source-id]").forEach(node => {
			const sourceId = node.getAttribute("data-source-id");
			if (!sourceId) return;
			if (!nextIndex.has(sourceId)) {
				nextIndex.set(sourceId, []);
			}
			nextIndex.get(sourceId).push(node);
		});
		clearAppliedHighlightNodes();
		sourceNodeIndex.value = nextIndex;
	};

	const nodesForSourceId = sourceId => {
		if (!sourceId) return [];
		return sourceNodeIndex.value.get(String(sourceId)) || [];
	};

	const applyHighlightGroup = (sourceIds, group) => {
		clearAppliedHighlightNodes(group);
		const className = highlightClassByGroup[group];
		(sourceIds || []).forEach(id => {
			nodesForSourceId(id).forEach(node => {
				node.classList.add(className);
				appliedHighlightNodes[group].add(node);
			});
		});
	};

	const applyHighlights = () => {
		applyHighlightGroup(store.relatedHighlightedSourceIds, "relatedHighlighted");
		applyHighlightGroup(store.highlightedSourceIds, "highlighted");
		applyHighlightGroup(store.pinnedSourceIds, "pinned");
		applyHighlightGroup(store.pinnedRelatedSourceIds, "pinnedRelated");
	};

	const findSourceNode = sourceIds => {
		for (const id of sourceIds || []) {
			const node = nodesForSourceId(id)[0];
			if (node) return node;
		}
		return null;
	};

	const scrollArticlePaneToNode = node => {
		const root = divRef.value;
		if (!root || !node) return;
		const rootRect = root.getBoundingClientRect();
		const nodeRect = node.getBoundingClientRect();
		const targetTop = Math.max(
			0,
			root.scrollTop + nodeRect.top - rootRect.top - (root.clientHeight / 2) + (nodeRect.height / 2)
		);
		if (store.revealBehavior === "smooth" && root.scrollTo) {
			root.scrollTo({ top: targetTop, behavior: "smooth" });
			return;
		}
		root.scrollTop = targetTop;
	};

	const revealHighlightedSource = () => {
		const node = findSourceNode(store.revealSourceIds);
		if (!node) return;
		scrollArticlePaneToNode(node);
	};

	const handleSelection = content => {
		bus.emit(`${props.divId}_Event`, { content });
	};

	watch(
		() => [store.highlightedSourceIds, store.relatedHighlightedSourceIds, store.pinnedSourceIds, store.pinnedRelatedSourceIds],
		() => applyHighlights(),
		{ deep: true, flush: "sync" }
	);

	watch(
		() => store.revealRequestId,
		() => revealHighlightedSource(),
		{ flush: "sync" }
	);

	watch(
		() => article.value?.html,
		() => nextTick(() => {
			buildSourceNodeIndex();
			applyHighlights();
		})
	);

	onMounted(() => {
		nextTick(() => {
			buildSourceNodeIndex();
			applyHighlights();
		});
	});
</script>

<style scoped>
	.div0 {
		position: relative;
		min-height: 100%;
		background: #ffffff;
	}

	.article-title {
		margin: 14px 16px 6px;
		color: #172033;
		font-size: 20px;
		line-height: 1.25;
		font-weight: 760;
		letter-spacing: 0;
		overflow-wrap: anywhere;
	}

	#div1 .article-title {
		padding-right: 42px;
	}

	#div3 .article-title {
		padding-left: 42px;
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

	:deep([data-source-id].source-related-highlight) {
		background: rgba(255, 238, 163, 0.28);
		outline: 1px solid rgba(217, 144, 47, 0.22);
		border-radius: 2px;
	}

	:deep([data-source-id].source-pinned) {
		background: rgba(56, 103, 168, 0.16);
		outline: 2px solid rgba(56, 103, 168, 0.52);
		border-radius: 2px;
	}

	:deep([data-source-id].source-related-pinned) {
		background: rgba(255, 228, 117, 0.42);
		outline: 2px solid rgba(217, 144, 47, 0.42);
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

	@media (max-width: 1180px) {
		.article-title {
			margin: 11px 12px 4px;
			font-size: 17px;
			line-height: 1.22;
		}
	}

	@media (max-width: 760px) {
		.article-title {
			margin: 9px 10px 3px;
			font-size: 15px;
		}
	}
</style>
