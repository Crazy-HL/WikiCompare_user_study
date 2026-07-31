<template>
	<div :class="['div0', selectContentClass]" :id="divId" ref="divRef">
		<h1>{{ pageTitle }}</h1>

		<!-- 加载动画 -->
		<div v-if="loading" class="loading-container">
			<div class="loading-spinner"></div>
			<div class="loading-text">Loading...</div>
		</div>

		<!-- 错误信息 -->
		<div v-else-if="error" class="error-container">
			<div class="error-icon">⚠️</div>
			<div class="error-message">{{ error }}</div>
			<button class="retry-button" @click="fetchWikipediaContent">重试</button>
		</div>

		<!-- 文章内容 -->
		<div
			v-else
			class="showHtml wikipedia-content"
			v-html="pageHtml"
			@mouseup="handleSelection"></div>

		<!-- 遮罩层 -->
		<div v-if="showPopup[divId]" class="overlay" @click="closePopup"></div>

		<!-- 选中内容放大显示 -->
		<div v-if="showPopup[divId]" class="text-popup" @click="closePopup">
			<!-- 切换视图按钮 -->
			<div class="view-switcher">
				<button
					@click.prevent.stop="switchView('text')"
					:class="{ active: currentView === 'text' }"
					title="文本视图">
					<font-awesome-icon :icon="['fas', 'align-left']" />
				</button>

				<button
					@click.prevent.stop="switchView('visual')"
					:class="{ active: currentView === 'visual' }"
					title="可视化视图">
					<font-awesome-icon :icon="['fas', 'chart-bar']" />
				</button>
			</div>

			<!-- 文本视图 -->
			<div v-if="currentView === 'text'">
				<div
					v-if="isTable(selectedText[divId])"
					class="table-container"
					v-html="selectedText[divId]"></div>
				<div v-else>
					<p>{{ selectedText[divId] }}</p>
				</div>
			</div>

			<!-- 可视化视图 -->
			<div v-if="currentView === 'visual'" class="visualization-container">
				<div v-if="visualizationLoading" class="loading-spinner"></div>
				<div v-else-if="divId === 'div1'" class="chart-container1"></div>
				<div v-else class="chart-container2"></div>
			</div>
		</div>
	</div>
</template>

<script setup>
	import { ref, onMounted, onUnmounted, nextTick } from "vue";
	import bus from "@/js/eventBus.js";
	import HighlightText from "@/js/highlight"; // 导入高亮工具包
	import * as d3 from "d3";
	import {
		renderLineChart,
		renderBarChart,
		renderPieChart,
		renderNonVisualChart,
		renderRadarChart,
		renderStackedBarChart
	} from "@/js/chartUtils";

	const props = defineProps({
		pageTitle: String,
		divId: String,
		selectContentClass: String
	});

	const pageHtml = ref(""); // 文章 HTML 内容
	const loading = ref(true); // 加载状态
	const error = ref(""); // 错误信息
	const selectedText = ref({}); // 存储每个 div 的选中内容
	const showPopup = ref({}); // 存储每个 div 的弹窗显示状态
	const divRef = ref(null); // `Div1` 或 `Div3` 的 DOM 参考
	const currentView = ref("text"); // 当前视图模式：text 或 visual
	const visualizationLoading = ref(false); // 可视化图表加载状态

	// **获取 Wikipedia 页面**
	const fetchWikipediaContent = async () => {
		try {
			const apiUrl = `https://en.wikipedia.org/api/rest_v1/page/html/${encodeURIComponent(
				props.pageTitle
			)}`;
			const response = await fetch(apiUrl);
			if (!response.ok) throw new Error("Failed to fetch data");

			const html = await response.text();

			// 解析 HTML
			const parser = new DOMParser();
			const doc = parser.parseFromString(html, "text/html");

			// 动态注入 Wikipedia 样式
			const styles = Array.from(doc.querySelectorAll('link[rel="stylesheet"]'));
			styles.forEach(link => {
				if (!document.querySelector(`link[href="${link.href}"]`)) {
					const styleTag = document.createElement("link");
					styleTag.rel = "stylesheet";
					styleTag.href = link.href;
					document.head.appendChild(styleTag);
				}
			});

			// 仅获取正文部分
			const contentElement = doc.querySelector("body");
			if (!contentElement) throw new Error("Content not found");

			pageHtml.value = contentElement.innerHTML;

			// 手动引入 Wikipedia CSS
			injectWikipediaStyles();
		} catch (err) {
			error.value = "Error fetching Wikipedia content: " + err.message;
		} finally {
			loading.value = false;
		}
	};

	// **手动引入 Wikipedia CSS**
	const injectWikipediaStyles = () => {
		const wikipediaStyles = [
			"https://en.wikipedia.org/w/load.php?modules=site.styles",
			"https://en.wikipedia.org/w/load.php?modules=ext.cite.styles",
			"https://en.wikipedia.org/w/load.php?modules=ext.scribunto.styles",
			"https://en.wikipedia.org/w/load.php?modules=skins.vector.styles"
		];

		wikipediaStyles.forEach(url => {
			if (!document.querySelector(`link[href="${url}"]`)) {
				const styleTag = document.createElement("link");
				styleTag.rel = "stylesheet";
				styleTag.href = url;
				document.head.appendChild(styleTag);
			}
		});
	};

	// **高亮并放大选中文字**
	const handleSelection = () => {
		// 如果弹出框已经显示并且有内容，则不更新
		if (showPopup.value[props.divId] && selectedText.value[props.divId]) {
			console.log("弹出框中已有内容，不更新");
			return;
		}

		const selection = window.getSelection();
		if (!selection.rangeCount) {
			console.log("没有选中内容");
			return;
		}

		const range = selection.getRangeAt(0);
		const selectedHtml = range.cloneContents();

		// 创建临时容器
		const tempDiv = document.createElement("div");
		tempDiv.appendChild(selectedHtml);

		// 判断选中的内容是否包含表格等 HTML 元素
		const table = tempDiv.querySelector("table");
		if (table) {
			console.log(`${props.divId}选中了表格内容`);
			table.classList.add("custom-table");
			selectedText.value[props.divId] = tempDiv.innerHTML; // 根据 divId 存储选中内容
		} else {
			const text = selection.toString().trim();
			if (!text) {
				console.log("选中的文字为空");
				return;
			}
			console.log(`${props.divId}选中的文字:`, text);
			selectedText.value[props.divId] = text; // 根据 divId 存储选中内容
		}

		showPopup.value[props.divId] = true; // 根据 divId 显示弹窗
		currentView.value = "text"; // 默认显示文本视图

		// 传递选中内容
		bus.emit(`${props.divId}Event`, { content: selection.toString() });

		// 确保弹窗位置更新
		nextTick(() => {
			updatePopupPosition();
		});
	};

	// **关闭弹出框**
	const closePopup = () => {
		showPopup.value[props.divId] = false; // 根据 divId 关闭弹窗
		selectedText.value[props.divId] = ""; // 根据 divId 清除选中内容

		// 根据 divId 清空对应的容器
		const container =
			props.divId === "div1" ? ".chart-container1" : ".chart-container2";
		d3.select(container).html("");
	};

	// **更新遮罩层和弹出框的位置**
	const updatePopupPosition = () => {
		if (showPopup.value[props.divId] && divRef.value) {
			const popup = divRef.value.querySelector(".text-popup");
			const overlay = divRef.value.querySelector(".overlay");
			if (popup && overlay) {
				const rect = divRef.value.getBoundingClientRect();
				const scrollTop = divRef.value.scrollTop;
				const scrollLeft = divRef.value.scrollLeft;

				// 动态调整遮罩层和弹出框的位置
				overlay.style.top = `${scrollTop}px`;
				overlay.style.left = `${scrollLeft}px`;
				overlay.style.width = `${divRef.value.clientWidth}px`;
				overlay.style.height = `${divRef.value.clientHeight}px`;

				popup.style.top = `${rect.height / 2 + scrollTop}px`;
				popup.style.left = `${rect.width / 2 + scrollLeft}px`;
			}
		}
	};

	// **判断是否是表格内容**
	const isTable = content => {
		// 判断选中内容是否包含 <table> 标签
		return /<table.*?>.*?<\/table>/s.test(content);
	};

	// **切换视图**
	const switchView = async view => {
		currentView.value = view;
		if (view === "visual") {
			visualizationLoading.value = true;
			await processText(); // 调用后端处理文本并渲染图表
			visualizationLoading.value = false;
		}
	};

	// 获取可视化 JSON 数据
	async function processText() {
		try {
			api.post(
				"process_text",
				{ text: selectedText.value[props.divId].toString().trim() }, // 使用对应 divId 的选中内容
				data => {
					if (data.error) {
						console.error("后端返回的错误:", data.error);
						alert(`处理文章内容时出错: ${data.message}`);
						return;
					}

					const jsonData = data.json_data;
					console.log("后端返回的数据:", jsonData);

					// 根据 divId 选择容器
					const container =
						props.divId === "div1" ? ".chart-container1" : ".chart-container2";

					if (data.data_type === "Non-Visual") {
						renderNonVisualChart(container, data, {
							message: "当前数据无法可视化"
						});
					} else {
						renderChart(jsonData, data.chart_classification);
					}
				}
			);
		} catch (error) {
			console.error("处理文章内容时出错:", error);
			alert("处理文章内容时出错，请稍后重试");
		}
	}

	// 渲染图表
	function renderChart(rawJsonData, chartType) {
		if (!rawJsonData || typeof rawJsonData !== "object" || !rawJsonData.data) {
			const container =
				props.divId === "div1" ? ".chart-container1" : ".chart-container2";
			renderNonVisualChart(container, rawJsonData, {
				message: "JSON 数据无效"
			});
			console.error("JSON 数据无效:", rawJsonData);
			return;
		}

		// 根据 divId 选择容器
		const container =
			props.divId === "div1" ? ".chart-container1" : ".chart-container2";

		// 清空之前的图表
		d3.select(container).html("");

		const data = rawJsonData.data;
		const options = rawJsonData.options || {};

		// 根据图表类型渲染
		if (chartType === "Line Chart") {
			renderLineChart(container, data, options);
		} else if (chartType === "Bar Chart") {
			renderBarChart(container, data, options);
		} else if (chartType === "Pie Chart") {
			renderPieChart(container, data, options);
		} else if (chartType === "Stacked Bar Chart") {
			renderStackedBarChart(container, data, options);
		} else {
			console.error("未知的图表类型:", chartType);
		}
	}

	// **组件挂载后加载 Wikipedia 内容**
	onMounted(() => {
		fetchWikipediaContent();

		// 绑定当前 div 的 mouseup 事件
		const targetDiv = divRef.value;
		if (targetDiv) {
			targetDiv.addEventListener("mouseup", handleSelection);
		}

		// 监听父容器滚动事件
		if (divRef.value) {
			divRef.value.addEventListener("scroll", updatePopupPosition);
		}
	});

	// **组件卸载时解绑事件**
	onUnmounted(() => {
		// 解绑当前 div 的 mouseup 事件
		const targetDiv = divRef.value;
		if (targetDiv) {
			targetDiv.removeEventListener("mouseup", handleSelection);
		}

		// 解绑父容器滚动事件
		if (divRef.value) {
			divRef.value.removeEventListener("scroll", updatePopupPosition);
		}
	});
</script>

<style scoped>
	h1 {
		text-align: center;
	}

	/* 文章容器 */
	.div0 {
		position: relative; /* 关键：父容器设置为 relative */
		width: 55%;
		max-width: 100%;
		max-height: 100%;
		overflow: auto; /* 关键：允许滚动 */
		padding: 20px;
		background-color: #ffffff;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	#div1,
	#div3 {
		width: 55%;
		max-width: 100%;
		max-height: 100%;
		overflow: auto;
		padding: 20px;
		background-color: #ffffff;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.showHtml {
		width: 100%;
		height: 100%;
		overflow: auto;
	}
	/* Wikipedia 内容 */
	.wikipedia-content {
		max-width: 800px;
		margin: 0 auto;
		padding: 20px;
		font-family: sans-serif;
		font-size: 0.6vw;
	}

	/* 遮罩层（固定在 Div1 或 Div3 内部） */ /* 遮罩层（固定在 Div1 或 Div3 内部） */
	.overlay {
		position: absolute; /* 关键：相对于父容器定位 */
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(255, 255, 255, 0.1); /* 半透明背景 */
		backdrop-filter: blur(10px); /* 背景模糊效果 */
		z-index: 90;
		animation: fadeIn 0.3s ease-in-out;
	}

	/* 选中内容的弹出框（固定在 Div1 或 Div3 内部） */
	.text-popup {
		position: absolute; /* 关键：相对于父容器定位 */
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 90%; /* 宽度占 Div1 或 Div3 的 80% */
		max-height: 80vh; /* 限制最大高度 */
		overflow: auto; /* 添加滚动条 */
		background: rgba(255, 255, 255, 0.98); /* 更亮的背景 */
		padding: 25px; /* 增加内边距 */
		box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.4); /* 更明显的阴影 */
		border-radius: 12px; /* 圆角更大 */
		text-align: center;
		font-size: 0.8vw; /* 固定字体大小 */
		font-weight: 500; /* 中等字体粗细 */
		line-height: 1.6; /* 增加行高 */
		color: #333; /* 更深的字体颜色 */
		z-index: 100;
		cursor: pointer;
		backdrop-filter: blur(20px); /* 更强烈的模糊效果 */
		animation: fadeIn 0.3s ease-in-out;
		border: 1px solid rgba(255, 255, 255, 0.2); /* 添加边框 */
		margin: 0;
	}

	/* 弹出框内的表格容器 */
	.table-container {
		width: 100%;
		overflow: auto;
		font-family: "Arial", sans-serif; /* 自定义字体 */
	}

	/* 自定义表格样式 */
	.table-container table {
		width: 100%;
		border-collapse: collapse;
		margin: 0 auto;
		background-color: #fff;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		overflow: hidden;
		font-size: 14px; /* 自定义字体大小 */
	}

	.table-container th,
	.table-container td {
		padding: 12px 15px;
		text-align: left;
		border-bottom: 1px solid #e0e0e0;
	}

	.table-container th {
		background-color: #f8f9fa;
		font-weight: 600;
		color: #333;
	}

	.table-container tr:last-child td {
		border-bottom: none; /* 移除最后一行的下边框 */
	}

	.table-container tr:nth-child(even) {
		background-color: #f9f9f9; /* 偶数行背景色 */
	}

	.table-container tr:hover {
		background-color: #f1f1f1; /* 鼠标悬停效果 */
	}

	/* 弹出框内的段落 */
	.text-popup p {
		margin: 0;
		padding: 10px 15px;
		font-size: 1.2rem;
		color: #333;
		text-align: justify; /* 让文本两端对齐 */
		line-height: 1.8; /* 增加行高，提高可读性 */
		word-break: break-word; /* 长单词自动换行，防止溢出 */
		white-space: pre-wrap; /* 保留原段落格式 */
		max-width: 90%; /* 限制最大宽度，避免过长 */
		border-left: 4px solid #3498db; /* 添加左侧蓝色边框，强调数据段落 */
		background: rgba(255, 255, 255, 0.9); /* 增加一点背景透明度 */
		box-shadow: inset 2px 2px 8px rgba(0, 0, 0, 0.05); /* 添加内阴影，使文本框更有层次感 */
	}

	/* 加载动画容器 */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 200px;
	}

	/* 加载动画 */
	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #3498db;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	/* 加载文字 */
	.loading-text {
		margin-top: 10px;
		font-size: 16px;
		color: #3498db;
	}

	/* 错误信息容器 */
	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 20px;
		background-color: #fff3f3;
		border: 1px solid #ffcccc;
		border-radius: 8px;
		animation: fadeIn 0.5s ease;
	}

	/* 错误图标 */
	.error-icon {
		font-size: 48px;
		color: #ff6b6b;
		margin-bottom: 10px;
	}

	/* 错误信息 */
	.error-message {
		font-size: 16px;
		color: #ff6b6b;
		text-align: center;
		margin-bottom: 20px;
	}

	/* 重试按钮 */
	.retry-button {
		padding: 10px 20px;
		background-color: #ff6b6b;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		transition: background-color 0.3s ease;
	}

	.retry-button:hover {
		background-color: #ff4c4c;
	}

	.retry-button:active {
		background-color: #ff3333;
	}

	/* 错误信息淡入动画 */
	@keyframes fadeIn {
		0% {
			opacity: 0;
			transform: translateY(-10px);
		}
		100% {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* 选中文本的高亮样式 */
	::selection {
		background-color: yellow;
		color: black;
	}

	/* 使用 ::v-deep 穿透 scoped 样式 */
	::v-deep .custom-table {
		width: 100%;
		border-collapse: collapse;
		margin: 5px auto;
		background-color: #ffffff;
		border: 1px solid #0077b6; /* 外边框颜色 */
		border-radius: 8px;
		overflow: hidden;
		font-family: "Arial", sans-serif;
		font-size: 16px; /* 设置整体字体大小 */
		color: #333333; /* 设置默认文字颜色 */
	}

	/* 表头样式 */
	::v-deep .custom-table th {
		background-color: #0077b6; /* 深蓝色表头 */
		font-weight: bold;
		color: #ffffff; /* 文字白色 */
		text-align: left;
		padding: 12px;
		border: 1px solid #0077b6; /* 表头单元格边框 */
		font-size: 18px; /* 表头字体稍大，增强层次感 */
	}

	/* 单元格样式 */
	::v-deep .custom-table th,
	::v-deep .custom-table td {
		padding: 12px;
		border: 1px solid #0077b6; /* 统一的单元格边框 */
		font-size: 16px; /* 调整字体大小 */
	}

	/* 悬停行高亮 */
	::v-deep .custom-table tr:hover {
		background-color: #cbe8f6; /* 浅蓝色 */
		transition: background-color 0.3s ease-in-out;
	}
	/* 新增样式：视图切换按钮 */
	.view-switcher {
		display: flex;
		justify-content: center;
		margin-bottom: 20px;
	}

	.view-switcher button {
		padding: 25px;
		margin: 0 5px;
		border: none;
		border-radius: 50%; /* 圆形按钮 */
		background-color: #f0f0f0;
		cursor: pointer;
		transition: background-color 0.3s ease, transform 0.2s ease;
		width: 36px; /* 固定宽度 */
		height: 36px; /* 固定高度 */
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.view-switcher button:hover {
		background-color: #ddd;
		transform: scale(1.1); /* 悬停时放大 */
	}

	.view-switcher button.active {
		background-color: #0077b6;
		color: white;
	}

	.view-switcher button i {
		font-size: 16px; /* 图标大小 */
		color: inherit; /* 继承按钮颜色 */
	}

	/* 可视化容器 */
	.visualization-container {
		width: 100%;
		height: 300px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>
