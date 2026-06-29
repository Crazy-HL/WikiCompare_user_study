<template>
	<div class="citation-list" v-if="citations?.length">
		<button
			v-for="citation in citations"
			:key="citation.id"
			class="citation-chip"
			@mouseenter="store.highlight(citation.sourceIds)"
			@mouseleave="store.clearHighlight()"
			@click="pinCitation(citation)">
			{{ citation.label }}
		</button>
	</div>
</template>

<script setup>
	import { sessionStore as store } from "@/js/sessionStore";

	defineProps({ citations: Array });

	const pinCitation = citation => {
		store.pin(citation.sourceIds);
		const firstId = citation.sourceIds?.[0];
		if (!firstId) return;
		requestAnimationFrame(() => {
			document
				.querySelector(`[data-source-id="${CSS.escape(firstId)}"]`)
				?.scrollIntoView({ behavior: "smooth", block: "center" });
		});
	};
</script>

<style scoped>
	.citation-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 8px;
	}

	.citation-chip {
		border: 1px solid #93c5fd;
		background: #eff6ff;
		color: #1d4ed8;
		border-radius: 999px;
		padding: 4px 9px;
		font-size: 12px;
		cursor: pointer;
	}
</style>
