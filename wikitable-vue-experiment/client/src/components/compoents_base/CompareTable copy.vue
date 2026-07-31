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
				<h3>{{ currentChart.title }} - {{ currentChart.field.key }}</h3>
				<div class="chart-container">
					<FullChart
						:field="currentChart.data"
						:type="currentChart.field.type"
						:visualization="currentChart.field.visualization" />
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
	const COMPARABLE_FIELDS = [
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
			key: "GDP growth",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "line-chart",
			legend: "GDP年增长率（%）"
		},
		{
			key: "Inflation (CPI)",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "pie-chart",
			legend: "消费者价格指数变化"
		},
		{
			key: "GDP rank",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "全球GDP排名"
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

		// 返回两边最大值中的较大者，并增加10%的缓冲空间
		return Math.max(leftMax, rightMax) * 1.1 || 1; // 避免除以0
	};

	// 获取图表props
	const getChartProps = (infobox, field) => {
		return {
			field: getField(infobox, field.key),
			type: field.type,
			visualization: field.visualization,
			unifiedMax: getUnifiedMaxValue(field.key), // 传递统一的最大值
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

		// 找到分数最高的字段进行自动对比
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
		// console.log(`[getField] 开始提取字段: ${fieldKey}`);
		// console.log(
		// 	"[getField] 输入的infobox结构:",
		// 	JSON.stringify(infobox, null, 2)
		// );

		if (!infobox?.data) {
			console.warn("[getField] 警告: infobox.data不存在");
			return [];
		}

		// 深度搜索字段函数
		const deepFind = (obj, key, path = []) => {
			if (obj[key] !== undefined) {
				// console.log(`[getField] 在路径 ${path.join(".")} 找到字段 ${key}`);
				return obj[key];
			}

			for (const [k, v] of Object.entries(obj)) {
				if (typeof v === "object" && v !== null) {
					const found = deepFind(v, key, [...path, k]);
					if (found !== undefined) return found;
				}
			}
			return undefined;
		};

		const fieldData = deepFind(infobox.data, fieldKey);
		// console.log(`[getField] 提取的原始fieldData:`, fieldData);

		if (fieldData === undefined) {
			console.warn(`[getField] 警告: 未找到字段 ${fieldKey}`);
			return [];
		}

		// 统一处理为数组
		const processItem = item => {
			// console.log("[getField] 正在处理项目:", item);

			// 临时修复：处理特定的GDP growth数据问题
			if (
				fieldKey === "GDP growth" &&
				typeof item === "object" &&
				item.raw === "0.6% ()"
			) {
				// console.log("[getField] 应用临时修复到0.6%数据项");
				item = {
					...item,
					raw: "0.6% (2025)", // 修正为不带f的年份格式
					year: 2025 // 设为数字类型的2025
				};
			}

			// 处理基本类型
			if (typeof item !== "object" || item === null) {
				const result = {
					value: item,
					raw: String(item),
					year: null,
					unit: null,
					currency: null,
					extracted: false
				};
				// console.log("[getField] 基本类型处理结果:", result);
				return result;
			}

			// 增强的年份提取
			let year = item.year;
			let raw = item.raw || String(item.value || JSON.stringify(item));

			if (!year && raw) {
				// 支持日期格式: (2023), (2024f), [2023], 2023年, 2023, 2023-2024等
				const yearMatch = raw.match(
					/(?:^|[\(\[])(\d{4})(?:[a-zA-Z]*|[\)\]])|(\d{4})年|(\d{4})(?=%|$)/
				);
				if (yearMatch) {
					// 提取年份数字部分（去掉可能的后缀字母如f）
					const yearStr = (
						yearMatch[1] ||
						yearMatch[2] ||
						yearMatch[3] ||
						""
					).replace(/[^0-9]/g, "");
					year = yearStr ? parseInt(yearStr) : null;
				}
				// console.log(`[getField] 从raw "${raw}" 中提取年份:`, year);
			}

			const result = {
				value: item.value !== undefined ? item.value : item,
				raw: raw,
				unit: item.unit || null,
				year: year,
				currency: item.currency || null,
				extracted: item.extracted !== false
			};

			// 如果是百分比类型，确保unit有值
			if (fieldKey === "GDP growth" || fieldKey === "Inflation (CPI)") {
				if (!result.unit && typeof result.value === "number") {
					result.unit = "%";
					if (!raw.includes("%")) {
						result.raw = `${result.value}%` + (year ? ` (${year})` : "");
					}
				}
			}

			// console.log("[getField] 对象处理结果:", result);
			return result;
		};

		const result = Array.isArray(fieldData)
			? fieldData.map(processItem)
			: [processItem(fieldData)];

		// console.log(`[getField] 最终提取结果(${fieldKey}):`, result);
		return result;
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
		const comparedPairs = [];

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

				comparedPairs.push({
					leftNum,
					rightNum,
					isOpposite,
					relativeDiff,
					score
				});

				if (score > maxScore) maxScore = score;
			});
		});

		const weight = field.key.toLowerCase().includes("gdp growth") ? 3 : 1;
		const finalScore = Math.min(100, Math.round(maxScore * weight));

		return finalScore;
	};

	const getFieldWeight = fieldKey => {
		const weights = {
			GDP: 1.5,
			Population: 1.3,
			"GDP growth": 2.0,
			Inflation: 1.8,
			Labor: 1.2
		};

		for (const [key, weight] of Object.entries(weights)) {
			if (fieldKey.toLowerCase().includes(key.toLowerCase())) {
				return weight;
			}
		}

		return 1.0;
	};

	const getHeatmapColor = score => {
		const maxScore = 100;
		const ratio = Math.min(score / maxScore, 1);
		const hue = (1 - ratio) * 120;
		return `hsl(${hue}, 80%, ${85 - ratio * 25}%)`;
	};

	const sortedFields = computed(() => {
		return sortedFieldsWithScores.value;
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

			// 计算完成后尝试自动对比
			tryAutoCompare();
		}
	};

	const showFullChart = (infobox, field) => {
		// console.log("data:", getField(infobox, field.key));
		currentChart.value = {
			title: infobox.title,
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

		// 合并两个数据源的数据
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
		console.log("combineData:", combinedData);
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
			minmax(80px, 100px)
			minmax(120px, 1fr);
		width: 100%;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
		max-height: 500px;
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
		height: 110px;
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
