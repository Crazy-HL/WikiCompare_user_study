<template>
	<!-- 大纲切换按钮 -->
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

	<!-- 大纲内容 -->
	<div v-if="isVisible" class="outline-container" :style="outlineStyle">
		<div class="outline">
			<ul>
				<li
					v-for="(item, index) in outline"
					:key="item.id"
					:class="{ linked: isLinked(item) }"
					:style="{
						paddingLeft: `${(item.level - 1) * 15}px`,
						borderLeft: isLinked(item)
							? `4px solid ${getBorderColor(item.id)}`
							: 'none'
					}">
					<a :href="'#' + item.id" @click.prevent="scrollToChapter(item.id)">{{
						item.text
					}}</a>
				</li>
			</ul>
		</div>
	</div>
</template>

<script setup>
	import { ref, watch, onMounted, onUnmounted } from "vue";
	import eventBus from "@/js/eventBus.js";

	const props = defineProps({
		content: String, // 文章 HTML
		divId: String // "div1" 或 "div3"
	});

	const isVisible = ref(false);
	const outline = ref([]);
	const buttonStyle = ref({});
	const outlineStyle = ref({});

	// **自定义关联数组**
	const linkedOutline = ref([
		{ leftId: "heading-0-div1", rightId: "heading-0-div3" },
		{ leftId: "heading-10-div1", rightId: "heading-11-div3" },
		{ leftId: "heading-13-div1", rightId: "heading-15-div3" },
		{ leftId: "heading-14-div1", rightId: "heading-16-div3" },
		{ leftId: "heading-17-div1", rightId: "heading-18-div3" },

		{ leftId: "heading-20-div1", rightId: "heading-27-div3" },

		{ leftId: "heading-23-div1", rightId: "heading-29-div3" }
	]);

	// **切换大纲的显示**
	const toggleOutline = () => {
		isVisible.value = !isVisible.value;
	};

	// **解析文章，提取 h1-h6 标题**
	const extractOutline = (content, containerId) => {
		if (!content) return [];
		const parser = new DOMParser();
		const doc = parser.parseFromString(content, "text/html");
		const headings = doc.querySelectorAll("h1, h2, h3, h4, h5, h6");

		return Array.from(headings).map((heading, index) => {
			const level = parseInt(heading.tagName.substring(1));
			const id = `heading-${index}-${containerId}`;
			heading.id = id;
			return { id, text: heading.textContent, level };
		});
	};

	// **监听 content 变化，更新大纲**
	watch(
		() => props.content,
		newContent => {
			outline.value = extractOutline(newContent, props.divId);

			// 提取另一个容器的大纲数据
			const otherContainerId = props.divId === "div1" ? "div3" : "div1";
			const otherContainer = document.getElementById(otherContainerId);
			if (otherContainer) {
				// 通过 eventBus 通知另一个大纲组件
				eventBus.emit("update-linked-outline", linkedOutline.value);
			}
		},
		{ immediate: true }
	);

	// **监听 eventBus，确保两边大纲同步**
	eventBus.on("update-linked-outline", newLinkedOutline => {
		linkedOutline.value = newLinkedOutline;
	});

	// **检查是否存在关联章节**
	const isLinked = item =>
		linkedOutline.value.some(
			linked => linked.leftId === item.id || linked.rightId === item.id
		);

	// **生成不同关联章节的边框颜色**
	const getBorderColor = id => {
		const linkedItem = linkedOutline.value.find(
			linked => linked.leftId === id || linked.rightId === id
		);
		if (linkedItem) {
			// 根据关联章节的索引生成不同的颜色
			const index = linkedOutline.value.indexOf(linkedItem);
			const colors = ["#FF6B6B", "#4ECDC4", "#FFD166", "#118AB2", "#073B4C"];
			return colors[index % colors.length];
		}
		return "transparent";
	};

	// **滚动到章节**
	const scrollToChapter = id => {
		// 跳转到当前文章的章节
		const element = document.getElementById(id);
		if (element) element.scrollIntoView({ behavior: "smooth" });

		// 找到关联章节并跳转
		const linkedItem = linkedOutline.value.find(
			linked => linked.leftId === id || linked.rightId === id
		);
		if (linkedItem) {
			const targetId =
				linkedItem.leftId === id ? linkedItem.rightId : linkedItem.leftId;
			eventBus.emit("scroll-to-chapter", targetId);
		}
	};

	// **监听 eventBus，确保两个组件同步跳转**
	eventBus.on("scroll-to-chapter", targetId => {
		const targetElement = document.getElementById(targetId);
		if (targetElement) targetElement.scrollIntoView({ behavior: "smooth" });
	});

	// **更新按钮和大纲的相对位置**
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

	// **窗口滚动时更新大纲位置**
	const handleScroll = () => {
		const referenceElement = document.getElementById(props.divId);
		if (!referenceElement) return;

		const scrollY = referenceElement.scrollTop;
		buttonStyle.value.top = `${scrollY + 10}px`;
		outlineStyle.value.top = `${scrollY + 50}px`;
	};

	// **初始化**
	onMounted(() => {
		outline.value = extractOutline(props.content, props.divId);
		updatePosition();
		const referenceElement = document.getElementById(props.divId);
		if (referenceElement)
			referenceElement.addEventListener("scroll", handleScroll);
	});

	// **组件销毁时移除事件**
	onUnmounted(() => {
		const referenceElement = document.getElementById(props.divId);
		if (referenceElement)
			referenceElement.removeEventListener("scroll", handleScroll);
		eventBus.off("update-linked-outline");
		eventBus.off("scroll-to-chapter");
	});
</script>

<style scoped>
	/* **按钮样式** */
	.toggle-btn {
		padding: 10px;
		border-radius: 50%;
		cursor: pointer;
		z-index: 2000;
		background-color: #0077b6;
		color: white;
		border: none;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		transition: all 0.3s ease-in-out;
	}

	/* **大纲样式** */
	.outline-container {
		background: white;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		padding: 15px;
		max-height: 80vh;
		overflow-y: auto;
		width: 260px;
		transition: all 0.3s ease-in-out;
	}

	.outline ul {
		list-style-type: none;
		padding-left: 0;
	}

	.outline li {
		margin-bottom: 8px;
		font-size: 14px;
		transition: padding-left 0.2s ease-in-out;
	}

	/* **关联章节样式** */
	.outline li.linked {
		border-left: 4px solid;
	}

	.outline li a {
		text-decoration: none;
		color: #0077b6;
	}

	.outline li a:hover {
		text-decoration: underline;
		color: #005f8a;
	}
</style>
