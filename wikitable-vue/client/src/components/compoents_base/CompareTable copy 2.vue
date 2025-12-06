<template>
	<div class="compare-container">
		<!-- 加载状态提示 -->
		<div v-if="isInitializing" class="initial-loading">
			<div class="loading-spinner"></div>
			<p>正在准备数据对比...</p>
		</div>

		<!-- 主对比表格 -->
		<div class="comparison-grid">
			<div class="header left-column">
				{{ leftInfobox.title }}
			</div>
			<div class="header middle-column">对比属性</div>
			<div class="header right-column">
				{{ rightInfobox.title }}
			</div>

			<template v-for="field in sortedFields" :key="field.key">
				<div
					class="cell left-column"
					@mouseover="hoverInfobox(leftInfobox, field.key, 'left')"
					@mouseout="unhoverInfobox('left')"
					@click="showFullChart(leftInfobox, field)">
					<SimpleChart v-bind="getChartProps(leftInfobox, field)" />
				</div>
				<div
					class="cell middle-column"
					@mouseover="hoverBothInfoboxes(field.key)"
					@mouseout="unhoverBothInfoboxes()">
					<div class="field-name">{{ field.key }}</div>
					<div class="field-type">{{ field.typeLabel }}</div>
					<div class="icon-actions">
						<span
							class="icon-btn compare"
							title="对比分析"
							@click="handleMiddleColumnClick(field)">
							⚖️
						</span>
						<span
							class="icon-btn merge"
							title="合并图表"
							@click="showCombinedChart(field)">
							📊
						</span>
					</div>
				</div>
				<div
					class="cell right-column"
					@mouseover="hoverInfobox(rightInfobox, field.key, 'right')"
					@mouseout="unhoverInfobox('right')"
					@click="showFullChart(rightInfobox, field)">
					<SimpleChart v-bind="getChartProps(rightInfobox, field)" />
				</div>
			</template>
		</div>

		<!-- 全屏图表模态框 -->
		<div
			v-if="showFullChartModal"
			class="full-chart-modal"
			@click.self="closeFullChart">
			<div class="modal-content">
				<button class="close-btn" @click="closeFullChart">×</button>
				<!-- <h3>{{ currentChart.title }}</h3> -->
				<div class="chart-container">
					<template v-if="currentChart.field.combined">
						<CombinedChart
							:data="currentChart.data"
							:fieldKey="currentChart.field.key"
							:sources="currentChart.field.sources" />
					</template>
					<template v-else>
						<FullChart
							:field="currentChart.data"
							:type="currentChart.field.type"
							:visualization="currentChart.field.visualization" />
					</template>
				</div>
				<div class="chart-legend" v-if="currentChart.field.legend">
					{{ currentChart.field.legend }}
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
	import { ref, computed, onMounted, watch, onUnmounted } from "vue";
	import SimpleChart from "./SimpleChart.vue";
	import FullChart from "./FullChart.vue";
	import CombinedChart from "./charts/CombinedChart.vue";
	import bus from "@/js/eventBus.js";

	const props = defineProps({
		div1RawData: Object,
		div3RawData: Object
	});

	const emit = defineEmits(["compareAttribute"]);

	// 状态变量
	const leftInfobox = ref({ title: "", type: "", data: {} });
	const rightInfobox = ref({ title: "", type: "", data: {} });
	const showFullChartModal = ref(false);
	const currentChart = ref({
		title: "",
		field: {},
		data: []
	});
	const isInitializing = ref(true);
	const hasAutoCompared = ref(false);
	const leftDataLoaded = ref(false);
	const rightDataLoaded = ref(false);
	const sortedFieldsWithScores = ref([]);

	// 可比较字段配置
	// 可比较字段配置（顺序即显示顺序）
	const COMPARABLE_FIELDS = [
		{
			key: "GDP growth",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "line-chart",
			legend: "GDP年增长率（%）"
		},
		{
			key: "Export goods",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "stacked-chart",
			legend: "出口商品（%）"
		},
		{
			key: "Import goods",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "stacked-chart",
			legend: "进口商品（%）"
		},
		{
			key: "GDP",
			type: "number",
			typeLabel: "数值(美元)",
			visualization: "bar-chart",
			legend: "国内生产总值（单位：万亿美元）"
		},
		{
			key: "Population",
			type: "number",
			typeLabel: "数值(人)",
			visualization: "bar-chart",
			legend: "人口数量（单位：亿人）"
		},
		{
			key: "Labor force by occupation",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "pie-chart",
			legend: "按职业划分的劳动力"
		},
		{
			key: "Inflation (CPI)",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "pie-chart",
			legend: "消费者价格指数变化"
		},

		{
			key: "Main export partners",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "stacked-chart",
			legend: "按职业划分的劳动力"
		},
		{
			key: "GDP rank",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "全球GDP排名"
		},
		{
			key: "Main industries",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "stacked-chart",
			legend: "主要产业（%）"
		},
		{
			key: "Main export partners",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "stacked-chart",
			legend: "主要出口伙伴（%）"
		},
		{
			key: "GDP per capita",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "人均国内生产总值"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Unemployment",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "失业"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		}
	];

	// 计算统一的最大值
	const getUnifiedMaxValue = fieldKey => {
		const leftValues = getField(leftInfobox.value, fieldKey)
			.map(v => (typeof v === "object" ? v.value ?? v.raw : v))
			.map(Number)
			.filter(n => !isNaN(n));

		const rightValues = getField(rightInfobox.value, fieldKey)
			.map(v => (typeof v === "object" ? v.value ?? v.raw : v))
			.map(Number)
			.filter(n => !isNaN(n));

		const leftMax = leftValues.length ? Math.max(...leftValues) : 0;
		const rightMax = rightValues.length ? Math.max(...rightValues) : 0;

		return Math.max(leftMax, rightMax) * 1.1 || 1;
	};

	// 获取图表props
	const getChartProps = (infobox, field) => {
		return {
			field: getField(infobox, field.key),
			type: field.type,
			visualization: field.visualization,
			unifiedMax: getUnifiedMaxValue(field.key),
			fieldKey: field.key
		};
	};

	// 自动对比方法
	const tryAutoCompare = () => {
		if (
			hasAutoCompared.value ||
			!leftDataLoaded.value ||
			!rightDataLoaded.value
		)
			return;

		isInitializing.value = true;
		hasAutoCompared.value = true;

		const mostSignificantField = sortedFieldsWithScores.value[0];
		if (mostSignificantField) {
			emit("compareAttribute", {
				fieldKey: mostSignificantField.key,
				leftData: getField(leftInfobox.value, mostSignificantField.key),
				rightData: getField(rightInfobox.value, mostSignificantField.key),
				leftTitle: leftInfobox.value.title,
				rightTitle: rightInfobox.value.title,
				fieldType: mostSignificantField.type,
				fieldLabel: mostSignificantField.typeLabel
			});
		}

		isInitializing.value = false;
	};

	const getField = (infobox, fieldKey) => {
		if (!infobox?.data) return [];

		const possibleKeys = [fieldKey];
		if (fieldKey.includes("Labor")) {
			possibleKeys.push(fieldKey.replace("Labor", "Labour"));
		}

		const deepFind = (obj, keys) => {
			for (const key of keys) {
				if (obj[key] !== undefined) return obj[key];
			}
			for (const [k, v] of Object.entries(obj)) {
				if (typeof v === "object" && v !== null) {
					const found = deepFind(v, keys);
					if (found !== undefined) return found;
				}
			}
			return undefined;
		};

		let fieldData = deepFind(infobox.data, possibleKeys);
		if (fieldData === undefined) return [];

		// 特定处理：右侧职业数据为多行字符串的情况
		if (
			typeof fieldData === "string" &&
			fieldKey.includes("Labor force by occupation")
		) {
			const lines = fieldData
				.split("\n")
				.map(line => line.trim())
				.filter(Boolean);
			fieldData = lines.map(line => {
				const [occupation, percentage] = line.split(/[:：]/);
				return {
					label: occupation.trim(),
					value: parseFloat(percentage),
					raw: line
				};
			});
		}

		// 统一为数组对象
		return Array.isArray(fieldData) ? fieldData : [fieldData];
	};

	const calculateDifferenceScore = field => {
		const leftValues = getField(leftInfobox.value, field.key)
			.map(v => (typeof v === "object" ? v.value ?? v.raw : v))
			.map(Number)
			.filter(n => !isNaN(n));

		const rightValues = getField(rightInfobox.value, field.key)
			.map(v => (typeof v === "object" ? v.value ?? v.raw : v))
			.map(Number)
			.filter(n => !isNaN(n));

		if (leftValues.length === 0 || rightValues.length === 0) {
			return 0;
		}

		let maxScore = 0;

		leftValues.forEach(leftNum => {
			rightValues.forEach(rightNum => {
				const isOpposite =
					(leftNum > 0 && rightNum < 0) || (leftNum < 0 && rightNum > 0);

				const absDiff = Math.abs(leftNum - rightNum);
				const avg = (Math.abs(leftNum) + Math.abs(rightNum)) / 2;
				const relativeDiff = avg > 0 ? absDiff / avg : 0;

				let score;
				if (isOpposite) {
					score = 90 + 10 * relativeDiff;
				} else {
					score = 10 + 40 * relativeDiff;
				}

				if (score > maxScore) maxScore = score;
			});
		});

		const weight = field.key.toLowerCase().includes("gdp growth") ? 3 : 1;
		return Math.min(100, Math.round(maxScore * weight));
	};

	const sortedFields = computed(() => {
		// return sortedFieldsWithScores.value;
		return comparableFields.value;
	});

	const comparableFields = computed(() => {
		return COMPARABLE_FIELDS.filter(field => {
			const leftVal = getField(leftInfobox.value, field.key);
			const rightVal = getField(rightInfobox.value, field.key);
			return leftVal.length > 0 || rightVal.length > 0;
		});
	});

	const tryCalculateScores = () => {
		if (leftDataLoaded.value && rightDataLoaded.value) {
			sortedFieldsWithScores.value = comparableFields.value
				.map(field => ({
					...field,
					score: calculateDifferenceScore(field)
				}))
				.sort((a, b) => {
					if (a.type !== "text" && b.type === "text") return -1;
					if (a.type === "text" && b.type !== "text") return 1;
					return b.score - a.score;
				});

			tryAutoCompare();
		}
	};

	const showFullChart = (infobox, field) => {
		currentChart.value = {
			title: `${infobox.title} - ${field.key}`,
			field: field,
			data: getField(infobox, field.key)
		};
		showFullChartModal.value = true;
	};

	const closeFullChart = () => {
		showFullChartModal.value = false;
	};

	const hoverInfobox = (infobox, fieldKey, side) => {
		bus.emit(`hover-${side}-infobox`, {
			fieldKey,
			infoboxTitle: infobox.title
		});
	};

	const unhoverInfobox = side => {
		bus.emit(`unhover-${side}-infobox`);
	};

	const hoverBothInfoboxes = fieldKey => {
		hoverInfobox(leftInfobox.value, fieldKey, "left");
		hoverInfobox(rightInfobox.value, fieldKey, "right");
	};

	const unhoverBothInfoboxes = () => {
		unhoverInfobox("left");
		unhoverInfobox("right");
	};

	const handleMiddleColumnClick = field => {
		emit("compareAttribute", {
			fieldKey: field.key,
			leftData: getField(leftInfobox.value, field.key),
			rightData: getField(rightInfobox.value, field.key),
			leftTitle: leftInfobox.value.title,
			rightTitle: rightInfobox.value.title,
			fieldType: field.type,
			fieldLabel: field.typeLabel
		});
	};

	const showCombinedChart = field => {
		const leftData = getField(leftInfobox.value, field.key);
		const rightData = getField(rightInfobox.value, field.key);

		// 合并两个数据源的数据并添加来源标识
		const combinedData = [
			...leftData.map(item => ({
				...item,
				source: leftInfobox.value.title,
				sourceType: "left"
			})),
			...rightData.map(item => ({
				...item,
				source: rightInfobox.value.title,
				sourceType: "right"
			}))
		];

		currentChart.value = {
			title: `合并图表 - ${field.key}`,
			field: {
				...field,
				visualization: "line-chart",
				combined: true,
				sources: {
					left: leftInfobox.value.title,
					right: rightInfobox.value.title
				}
			},
			data: combinedData
		};
		showFullChartModal.value = true;
	};

	const processInfoboxData = data => {
		if (!data) {
			console.warn("接收到空Infobox数据");
			return { title: "", type: "", data: {} };
		}
		return {
			title: data.title || "无标题",
			type: data.type || "未知类型",
			data: data.sections || {}
		};
	};

	onMounted(() => {
		bus.on("div1_InfoboxData", data => {
			leftInfobox.value = processInfoboxData(data);
			leftDataLoaded.value = true;
			tryCalculateScores();
		});

		bus.on("div3_InfoboxData", data => {
			rightInfobox.value = processInfoboxData(data);
			rightDataLoaded.value = true;
			tryCalculateScores();
		});
	});

	watch(
		[() => leftDataLoaded.value, () => rightDataLoaded.value],
		([leftLoaded, rightLoaded]) => {
			if (leftLoaded && rightLoaded) {
				tryCalculateScores();
			}
		}
	);

	onUnmounted(() => {
		bus.off("div1_InfoboxData");
		bus.off("div3_InfoboxData");
	});
</script>

<style scoped>
	/* 原有样式保持不变 */
	.compare-container {
		width: 100%;
		height: 100%;
		padding: 8px;
		box-sizing: border-box;
		position: relative;
	}

	.initial-loading {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(255, 255, 255, 0.8);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		z-index: 100;
	}

	.initial-loading p {
		margin-top: 10px;
		font-size: 14px;
		color: #666;
	}

	.loading-spinner {
		width: 30px;
		height: 30px;
		border: 3px solid #f3f3f3;
		border-top: 3px solid #4caf50;
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

	.comparison-grid {
		display: grid;
		grid-template-columns:
			minmax(120px, 1fr)
			minmax(80px, 150px)
			minmax(120px, 1fr);
		width: 100%;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
		max-height: 1500px;
		overflow-y: auto;
	}

	.header {
		padding: 8px 6px;
		background: #2c3e50;
		color: white;
		font-weight: bold;
		text-align: center;
		position: sticky;
		top: 0;
		z-index: 1;
		border-right: 1px solid #475569;
		min-height: 36px;
		font-size: 13px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.header.middle-column {
		padding: 8px 4px;
		background: #1e293b;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.cell {
		padding: 8px;
		height: 150px;
		border-bottom: 1px solid #e0e0e0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		position: relative;
		cursor: pointer;
		transition: all 0.3s ease;
		min-width: 0;
		overflow: hidden;
	}

	.left-column,
	.right-column {
		max-width: 100%;
	}

	.cell:hover {
		background-color: #f5f5f5;
	}

	.left-column:hover {
		background-color: #fff8e1;
	}

	.right-column:hover {
		background-color: #fff8e1;
	}

	.middle-column {
		position: relative;
		cursor: default;
		background-color: #f8f9fa;
		transition: background-color 0.2s;
	}

	.middle-column:hover {
		background-color: #e9ecef;
	}

	.field-name {
		font-weight: bold;
		margin-bottom: 4px;
		font-size: 12px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		text-align: center;
		width: 100%;
	}

	.field-type {
		color: #666;
		font-size: 11px;
		font-style: italic;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		text-align: center;
		width: 100%;
	}

	.icon-actions {
		display: flex;
		justify-content: center;
		gap: 15px;
		margin-top: 8px;
	}

	.icon-btn {
		font-size: 16px;
		cursor: pointer;
		opacity: 0.7;
		transition: all 0.2s;
	}

	.icon-btn:hover {
		opacity: 1;
		transform: scale(1.2);
	}

	.icon-btn.compare:hover {
		color: #4caf50;
	}

	.icon-btn.merge:hover {
		color: #2196f3;
	}

	.full-chart-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.3);
		backdrop-filter: blur(8px);
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 1000;
		animation: fadeIn 0.3s ease-out;
	}

	.modal-content {
		background: white;
		padding: 16px;
		border-radius: 8px;
		width: 85%;
		max-width: 800px;
		max-height: 85vh;
		position: relative;
		overflow-y: auto;
	}

	.chart-container {
		height: 60vh;
		width: 100%;
		margin: 16px 0;
	}

	.chart-legend {
		font-size: 13px;
		color: #666;
		text-align: center;
		margin-top: 12px;
		padding-top: 12px;
		border-top: 1px solid #eee;
	}

	.close-btn {
		position: absolute;
		top: 8px;
		right: 8px;
		font-size: 20px;
		background: none;
		border: none;
		cursor: pointer;
		color: #666;
	}

	.close-btn:hover {
		color: #333;
	}
</style>
