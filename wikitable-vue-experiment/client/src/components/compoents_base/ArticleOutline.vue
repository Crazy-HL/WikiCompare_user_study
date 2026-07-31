<template>
	<button @click="toggleOutline" class="toggle-btn" :style="buttonStyle" title="Article outline">
		<svg v-if="!isVisible" class="icon" viewBox="0 0 24 24">
			<path
				fill="currentColor"
				d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"></path>
		</svg>
		<svg v-else class="icon close" viewBox="0 0 24 24">
			<path fill="currentColor" d="M6 18L18 6M6 6l12 12"></path>
		</svg>
	</button>

	<div v-if="isVisible" class="outline-container" :style="outlineStyle">
		<div class="outline">
			<ul>
				<li
					v-for="item in outlineItems"
					:key="item.id"
					:class="{ linked: isLinked(item.id) }"
					:style="{
						paddingLeft: `${Math.max((item.level || 1) - 1, 0) * 15}px`,
						borderLeft: isLinked(item.id)
							? `4px solid ${getBorderColor(item.id)}`
							: 'none'
					}">
					<a :href="'#' + item.id" @click.prevent="scrollToChapter(item.id)">
						{{ item.text }}
					</a>
					<span v-if="isLinked(item.id)" class="linked-dot" title="Matched section"></span>
				</li>
			</ul>
		</div>
	</div>
</template>

<script setup>
	import { computed, onMounted, onUnmounted, ref } from "vue";
	import eventBus from "@/js/eventBus.js";

	const props = defineProps({
		outline: {
			type: Array,
			default: () => []
		},
		divId: String,
		matches: {
			type: Array,
			default: () => []
		}
	});

	const isVisible = ref(false);
	const buttonStyle = ref({});
	const outlineStyle = ref({});

	const outlineItems = computed(() => props.outline || []);

	const linkedPairs = computed(() =>
		(props.matches || [])
			.map(match => ({
				leftId: match.leftId || match.left || match.leftHeadingId,
				rightId: match.rightId || match.right || match.rightHeadingId
			}))
			.filter(match => match.leftId && match.rightId)
	);

	const toggleOutline = () => {
		isVisible.value = !isVisible.value;
	};

	const linkedPairFor = id =>
		linkedPairs.value.find(linked => linked.leftId === id || linked.rightId === id);

	const isLinked = id => Boolean(linkedPairFor(id));

	const getBorderColor = id => {
		const linkedItem = linkedPairFor(id);
		if (!linkedItem) return "transparent";
		const index = linkedPairs.value.indexOf(linkedItem);
		const colors = ["#ef4444", "#14b8a6", "#f59e0b", "#2563eb", "#475569"];
		return colors[index % colors.length];
	};

	const scrollToChapter = id => {
		scrollSourceIntoView(id, "smooth");
		const linkedItem = linkedPairFor(id);
		if (!linkedItem) return;
		const targetId = linkedItem.leftId === id ? linkedItem.rightId : linkedItem.leftId;
		eventBus.emit("scroll-to-chapter", { targetId, fromDivId: props.divId });
	};

	const handleScrollToChapter = payload => {
		const targetId = typeof payload === "string" ? payload : payload?.targetId;
		if (!targetId || payload?.fromDivId === props.divId) return;
		scrollSourceIntoView(targetId, "smooth");
	};

	const scrollSourceIntoView = (sourceId, behavior = "auto") => {
		const node = sourceNode(sourceId);
		if (!node) return;
		node.scrollIntoView({ behavior, block: "start", inline: "nearest" });
		node.classList.add("outline-target-flash");
		window.setTimeout(() => node.classList.remove("outline-target-flash"), 900);
	};

	const sourceNode = sourceId => {
		const root = document.getElementById(props.divId);
		if (!root || !sourceId) return null;
		return root.querySelector(`[data-source-id="${cssEscape(sourceId)}"]`);
	};

	const cssEscape = value => {
		if (window.CSS?.escape) return window.CSS.escape(value);
		return String(value).replace(/"/g, '\\"');
	};

	const updatePosition = () => {
		const isDiv1 = props.divId === "div1";
		buttonStyle.value = {
			position: "absolute",
			top: "11px",
			[isDiv1 ? "right" : "left"]: "12px"
		};
		outlineStyle.value = {
			position: "absolute",
			top: "48px",
			[isDiv1 ? "right" : "left"]: "12px",
			width: "260px",
			maxHeight: "80vh",
			overflowY: "auto",
			zIndex: "1000",
			background: "rgba(255, 255, 255, 0.97)",
			border: "1px solid #dbe3ee",
			borderRadius: "8px",
			boxShadow: "0 12px 30px rgba(15, 23, 42, 0.18)",
			padding: "15px"
		};
	};

	const handleScroll = () => {
		const referenceElement = document.getElementById(props.divId);
		if (!referenceElement) return;
		const scrollY = referenceElement.scrollTop;
		buttonStyle.value.top = `${scrollY + 11}px`;
		outlineStyle.value.top = `${scrollY + 48}px`;
	};

	onMounted(() => {
		updatePosition();
		eventBus.on("scroll-to-chapter", handleScrollToChapter);
		const referenceElement = document.getElementById(props.divId);
		referenceElement?.addEventListener("scroll", handleScroll);
	});

	onUnmounted(() => {
		eventBus.off("scroll-to-chapter", handleScrollToChapter);
		const referenceElement = document.getElementById(props.divId);
		referenceElement?.removeEventListener("scroll", handleScroll);
	});
</script>

<style scoped>
	.toggle-btn {
		padding: 7px;
		border-radius: 50%;
		cursor: pointer;
		z-index: 2000;
		background-color: #334155;
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.72);
		display: flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		box-shadow:
			0 1px 3px rgba(15, 23, 42, 0.16),
			0 5px 12px rgba(15, 23, 42, 0.12);
		transition: all 0.2s ease-in-out;
	}

	.toggle-btn:hover {
		background-color: #172033;
		transform: translateY(-1px);
	}

	.outline-container {
		background: rgba(255, 255, 255, 0.97);
		border: 1px solid #dbe3ee;
		border-radius: 8px;
		box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
		padding: 15px;
		max-height: 80vh;
		overflow-y: auto;
		width: 260px;
	}

	.outline ul {
		list-style-type: none;
		padding-left: 0;
	}

	.outline li {
		position: relative;
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 7px;
		font-size: 12px;
		line-height: 1.35;
	}

	.outline li a {
		flex: 1;
		text-decoration: none;
		color: #3867a8;
		overflow-wrap: anywhere;
	}

	.outline li a:hover {
		text-decoration: underline;
		color: #243447;
	}

	.linked-dot {
		width: 7px;
		height: 7px;
		border-radius: 999px;
		background: #5f8f3f;
	}

	:global(.outline-target-flash) {
		box-shadow: inset 3px 0 0 #5f8f3f;
		background: rgba(95, 143, 63, 0.12);
		transition: background 0.2s ease;
	}
</style>
