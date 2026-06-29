<template>
	<button @click="toggleOutline" class="toggle-btn" :style="buttonStyle">
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
		document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
		const linkedItem = linkedPairFor(id);
		if (!linkedItem) return;
		const targetId = linkedItem.leftId === id ? linkedItem.rightId : linkedItem.leftId;
		eventBus.emit("scroll-to-chapter", targetId);
	};

	const handleScrollToChapter = targetId => {
		document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth" });
	};

	const updatePosition = () => {
		const isDiv1 = props.divId === "div1";
		buttonStyle.value = {
			position: "absolute",
			top: "10px",
			[isDiv1 ? "right" : "left"]: "10px"
		};
		outlineStyle.value = {
			position: "absolute",
			top: "50px",
			[isDiv1 ? "right" : "left"]: "10px",
			width: "260px",
			maxHeight: "80vh",
			overflowY: "auto",
			zIndex: "1000",
			background: "white",
			borderRadius: "8px",
			boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
			padding: "15px"
		};
	};

	const handleScroll = () => {
		const referenceElement = document.getElementById(props.divId);
		if (!referenceElement) return;
		const scrollY = referenceElement.scrollTop;
		buttonStyle.value.top = `${scrollY + 10}px`;
		outlineStyle.value.top = `${scrollY + 50}px`;
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
		padding: 10px;
		border-radius: 50%;
		cursor: pointer;
		z-index: 2000;
		background-color: #2563eb;
		color: white;
		border: none;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		transition: all 0.2s ease-in-out;
	}

	.outline-container {
		background: white;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
		margin-bottom: 8px;
		font-size: 14px;
	}

	.outline li a {
		text-decoration: none;
		color: #2563eb;
	}

	.outline li a:hover {
		text-decoration: underline;
		color: #1d4ed8;
	}
</style>
