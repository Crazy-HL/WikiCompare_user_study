<template>
	<!-- 遮罩层 -->
	<div v-if="visible" class="overlay" @click="close"></div>

	<!-- 弹出框 -->
	<div v-if="visible" class="text-popup" @click.stop>
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
		<div v-show="currentView === 'text'">
			<div v-if="isTable" class="table-container" v-html="content"></div>
			<div v-else>
				<p>{{ content }}</p>
			</div>
		</div>

		<!-- 可视化视图 -->
		<div
			v-show="currentView === 'visual'"
			class="visualization-container"
			@dragstart="handleDragStart"
			@dragend="handleDragEnd"
			@dragenter="handleDragEnter"
			@dragleave="handleDragLeave"
			draggable="true"
			:class="{ dragging: isDragging, 'drag-over': isDragOver }">
			<div v-if="loading" class="loading-spinner"></div>
			<div v-else :class="containerClass"></div>
		</div>
	</div>
</template>

<script setup>
	import { ref, computed, onMounted, onUnmounted, watch } from "vue";
	import * as d3 from "d3";
	import bus from "@/js/eventBus.js";
	import {
		renderLineChart,
		renderBarChart,
		renderPieChart,
		renderNonVisualChart,
		renderRadarChart,
		renderStackedBarChart,
		renderScatterChart
	} from "@/js/chartUtils";

	const props = defineProps({
		visible: Boolean,
		content: String,
		containerClass: String,
		containerRef: String,
		sourceId: String // 新增：当前选中的章节 ID
	});

	const emit = defineEmits(["close"]);

	const currentView = ref("text");
	const loading = ref(false);
	const isChartRendered = ref(false);
	const cachedChartData = ref(null);
	const cachedChartType = ref(null);
	const isDragging = ref(false);
	const isDragOver = ref(false);

	const isTable = computed(() => {
		return /<table.*?>.*?<\/table>/s.test(props.content);
	});

	const close = () => {
		d3.select(`.${props.containerClass}`).html("");
		isChartRendered.value = false;
		cachedChartData.value = null;
		cachedChartType.value = null;
		emit("close");
	};

	// 监听 content 变化
	// watch(
	// 	() => props.content,
	// 	newContent => {
	// 		console.log("Popup content updated:", newContent); // 调试日志
	// 	}
	// );
	const switchView = async view => {
		currentView.value = view;
		if (view === "visual") {
			if (!isChartRendered.value) {
				loading.value = true;
				await processText();
				loading.value = false;
				isChartRendered.value = true;
			} else if (cachedChartData.value && cachedChartType.value) {
				renderChart(cachedChartData.value, cachedChartType.value);
			}
		}
	};

	async function processText() {
		try {
			api.post(
				"process_text",
				{ text: props.content.toString().trim() },
				data => {
					if (data.error) {
						console.error("后端返回的错误:", data.error);
						alert(`处理文章内容时出错: ${data.message}`);
						return;
					}

					const jsonData = data.json_data;
					console.log("后端返回的数据:", jsonData);

					cachedChartData.value = jsonData;
					cachedChartType.value = data.chart_classification;

					d3.select(`.${props.containerClass}`).html("");

					if (data.data_type === "Non-Visual") {
						renderNonVisualChart(`.${props.containerClass}`, data, {
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

	function renderChart(rawJsonData, chartType) {
		if (!rawJsonData || typeof rawJsonData !== "object") {
			renderNonVisualChart(`.${props.containerClass}`, rawJsonData, {
				message: "JSON 数据无效"
			});
			console.error("JSON 数据无效:", rawJsonData);
			return;
		}

		console.log("&&&rawJsonData:", rawJsonData);
		const data = rawJsonData.data;
		const options = rawJsonData.options || {};

		if (chartType === "Line Chart") {
			renderLineChart(`.${props.containerClass}`, data, options);
		} else if (chartType === "Bar Chart") {
			renderBarChart(`.${props.containerClass}`, rawJsonData);
		} else if (chartType === "Pie Chart") {
			renderPieChart(`.${props.containerClass}`, data, options);
		} else if (chartType === "Stacked Bar Chart") {
			renderStackedBarChart(`.${props.containerClass}`, data, options);
		} else if (chartType === "Radar Chart") {
			renderRadarChart(`.${props.containerClass}`, rawJsonData);
		} else if (chartType === "Scatter Chart") {
			renderScatterChart(`.${props.containerClass}`, rawJsonData);
		} else {
			console.error("未知的图表类型:", chartType);
		}
	}

	const handleDragStart = event => {
		isDragging.value = true;
		event.dataTransfer.setData(
			"application/json",
			JSON.stringify({
				chartData: cachedChartData.value,
				chartType: cachedChartType.value
			})
		);
		console.log("拖拽数据已设置:", cachedChartData.value);
	};

	const handleDragEnd = () => {
		isDragging.value = false;
		isDragOver.value = false;
	};

	const handleDragEnter = () => {
		isDragOver.value = true;
	};

	const handleDragLeave = () => {
		isDragOver.value = false;
	};

	const handleUpdateChart1 = data => {
		console.log("&&&data1:", data);
		const jsonData = JSON.parse(JSON.stringify(data.jsonData));
		d3.select(`.${props.containerClass}`).html("");
		renderChart(jsonData, data.chartType);
		isChartRendered.value = true;
		cachedChartData.value = jsonData;
		cachedChartType.value = data.chartType;
	};

	const handleUpdateChart3 = data => {
		console.log("&&&data3:", data);
		const jsonData = JSON.parse(JSON.stringify(data.jsonData));
		d3.select(`.${props.containerClass}`).html("");
		renderChart(jsonData, data.chartType);
		isChartRendered.value = true;
		cachedChartData.value = jsonData;
		cachedChartType.value = data.chartType;
	};

	onMounted(() => {
		console.log(props.containerClass + "挂载");
		bus.on("updateChart1", handleUpdateChart1);
		bus.on("updateChart3", handleUpdateChart3);
	});

	onUnmounted(() => {
		console.log(props.containerClass + "卸载");
		bus.off("updateChart1", handleUpdateChart1);
		bus.off("updateChart3", handleUpdateChart3);
	});
</script>

<style scoped>
	.overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		z-index: 90;
		animation: fadeIn 0.3s ease-in-out;
	}

	.text-popup {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 90%;
		max-height: 80vh;
		overflow: auto;
		background: rgba(255, 255, 255, 0.98);
		padding: 25px;
		box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.4);
		border-radius: 12px;
		text-align: center;
		font-size: 0.8vw;
		font-weight: 500;
		line-height: 1.6;
		color: #333;
		z-index: 100;
		cursor: pointer;
		backdrop-filter: blur(20px);
		animation: fadeIn 0.3s ease-in-out;
		border: 1px solid rgba(255, 255, 255, 0.2);
		margin: 0;
	}

	.view-switcher {
		display: flex;
		justify-content: center;
		margin-bottom: 20px;
	}

	.view-switcher button {
		padding: 25px;
		margin: 0 5px;
		border: none;
		border-radius: 50%;
		background-color: #f0f0f0;
		cursor: pointer;
		transition: background-color 0.3s ease, transform 0.2s ease;
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.view-switcher button:hover {
		background-color: #ddd;
		transform: scale(1.1);
	}

	.view-switcher button.active {
		background-color: #0077b6;
		color: white;
	}

	.visualization-container {
		width: 100%;
		height: 300px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: opacity 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
	}

	.visualization-container.dragging {
		opacity: 0.7;
		transform: scale(0.95);
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
	}

	.visualization-container.drag-over {
		border: 2px dashed #0077b6;
		background-color: rgba(0, 119, 182, 0.1);
	}

	.table-container {
		width: 100%;
		overflow: auto;
		font-family: "Arial", sans-serif;
	}

	.text-popup p {
		margin: 0;
		padding: 10px 15px;
		font-size: 1.2rem;
		color: #333;
		text-align: justify;
		line-height: 1.8;
		word-break: break-word;
		white-space: pre-wrap;
		max-width: 90%;
		border-left: 4px solid #3498db;
		background: rgba(255, 255, 255, 0.9);
		box-shadow: inset 2px 2px 8px rgba(0, 0, 0, 0.05);
	}

	::v-deep .custom-table {
		width: 80%;
		border-collapse: collapse;
		margin: 5px auto;
		background-color: #ffffff;
		border: 1px solid #0077b6;
		border-radius: 8px;
		overflow: hidden;
		font-family: "Arial", sans-serif;
		font-size: 16px; /* 调小字体大小 */
		color: #333333;
	}

	::v-deep .custom-table th {
		background-color: #0077b6;
		font-weight: bold;
		color: #ffffff;
		text-align: left;
		padding: 4px; /* 调小内边距 */
		border: 1px solid #0077b6;
		font-size: 18px; /* 调小标题字体大小 */
	}

	::v-deep .custom-table td {
		padding: 4px; /* 调小内边距 */
		border: 1px solid #0077b6;
		font-size: 16px; /* 调小内容字体大小 */
	}

	::v-deep .custom-table tr:hover {
		background-color: #cbe8f6;
		transition: background-color 0.3s ease-in-out;
	}
</style>
