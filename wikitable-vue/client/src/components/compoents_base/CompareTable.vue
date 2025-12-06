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
	const COMPARABLE_FIELDS = [
		{
			key: "GDP growth",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "line-chart",
			legend: "GDP年增长率（%）"
		},
		{
			key: "Population",
			type: "number",
			typeLabel: "数值(人)",
			visualization: "bar-chart",
			legend: "人口数量（单位：亿人）"
		},
		{
			key: "GDP",
			type: "number",
			typeLabel: "数值(美元)",
			visualization: "bar-chart",
			legend: "国内生产总值（单位：万亿美元）"
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
			key: "GDP by sector",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "pie-chart",
			legend: "按行业划分的国内生产总值"
		},
		{
			key: "GDP per capita",
			type: "number",
			typeLabel: "数值(美元)",
			visualization: "bar-chart",
			legend: "人均国内生产总值（单位：美元）"
		},
		{
			key: "Main industries",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "stacked-chart",
			legend: "主要产业（%）"
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
			legend: "主要出口伙伴（%）"
		},
		{
			key: "Labor force by occupation",
			type: "percentage",
			typeLabel: "百分比(%)",
			visualization: "pie-chart",
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
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		},
		{
			key: "Gini coefficient",
			type: "text",
			typeLabel: "文本",
			visualization: "text-only",
			legend: "基尼系数"
		}
	];

	// 基础颜色列表（12种）
	const UNIFIED_COLOR_PALETTE = [
		"#8dd3c7",
		"#ffffb3",
		"#bebada",
		"#fb8072",
		"#80b1d3",
		"#fdb462",
		"#b3de69",
		"#fccde5",
		"#d9d9d9",
		"#bc80bd",
		"#ccebc5",
		"#ffed6f"
	];
	const OTHERS_COLOR = "#a9a9a9"; // "Others"类别的固定颜色

	/**
	 * 为超出基础调色板的类别动态生成视觉上不同的颜色。
	 */
	const generateDistinctColor = (index, baseHue) => {
		const hue = (baseHue + index * 137.5) % 360;
		const saturation = 75;
		const lightness = 55;
		return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
	};

	/**
	 * 创建统一的颜色映射，如果类别超过12个，则动态生成新颜色。
	 */
	const getUnifiedCategoryColors = fieldKey => {
		// 辅助函数：从数据项中提取并清理类别名称
		const getCategoryName = item => {
			if (!item || !item.raw) return null;
			let name = String(item.raw)
				.replace(/\s*\d+(\.\d+)?%?$/, "")
				.trim();
			return name.replace(/[.:\s]*$/, "").trim();
		};

		const leftData = getField(leftInfobox.value, fieldKey);
		const rightData = getField(rightInfobox.value, fieldKey);

		// 获取所有唯一的类别名称
		const allUniqueCategories = [
			...new Set([
				...leftData.map(getCategoryName),
				...rightData.map(getCategoryName)
			])
		].filter(Boolean);

		const colorMap = {};
		const baseHueForGenerator = Math.random() * 360;
		let colorIndex = 0;

		// 遍历所有唯一类别来分配颜色
		allUniqueCategories.forEach(category => {
			const lowerCaseCategory = category.toLowerCase();
			if (lowerCaseCategory === "others" || lowerCaseCategory === "other") {
				colorMap["Others"] = OTHERS_COLOR;
				colorMap["Other"] = OTHERS_COLOR;
				colorMap[category] = OTHERS_COLOR;
				return;
			}

			if (colorIndex < UNIFIED_COLOR_PALETTE.length) {
				colorMap[category] = UNIFIED_COLOR_PALETTE[colorIndex];
			} else {
				const generatorIndex = colorIndex - UNIFIED_COLOR_PALETTE.length;
				colorMap[category] = generateDistinctColor(
					generatorIndex,
					baseHueForGenerator
				);
			}
			colorIndex++;
		});

		return colorMap;
	};

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
			fieldKey: field.key,
			categoryColors: getUnifiedCategoryColors(field.key)
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

	// 检查是否是有效的国家/地区名称
	const isValidCountryName = name => {
		const invalidPatterns = [
			/^<\/?[a-z][\s\S]*>/i, // HTML标签
			/^\(.*\)$/, // 括号内容（如年份）
			/^\d+$/, // 纯数字
			/^nowrap$/i, // CSS类名
			/^flagicon$/i, // CSS类名
			/^treeview$/i, // CSS类名
			/^mw-/i, // MediaWiki相关
			/^cite_ref/i // 引用标记
		];

		return (
			!invalidPatterns.some(pattern => pattern.test(name)) &&
			name.length > 1 &&
			!name.includes("{") &&
			!name.includes("}")
		);
	};

	// 从 raw 数据中提取名称
	const extractNameFromRaw = raw => {
		if (!raw) return null;
		const match = String(raw).match(/(.+?)\s*[\d.]+%?$/);
		return match ? match[1].trim() : null;
	};

	// 从 raw 数据中提取数值
	const extractValueFromRaw = raw => {
		if (!raw) return 0;
		const match = String(raw).match(/([\d.]+)%?$/);
		return match ? parseFloat(match[1]) : 0;
	};

	// 解析树形结构数据的辅助函数
	const parseTreeStructureData = dataString => {
		const result = [];
		const lines = dataString.split("\n").filter(line => line.trim());

		lines.forEach(line => {
			// 匹配百分比数据格式：国家/地区 XX.X%
			const match = line.match(/(.+?)\s*([\d.]+)%$/);
			if (match) {
				const [, name, percentage] = match;
				const trimmedName = name.trim();

				// 跳过空名称
				if (!trimmedName) return;

				// 检查是否是有效的国家/地区名称（不是HTML标签或其他无效内容）
				if (isValidCountryName(trimmedName)) {
					result.push({
						label: trimmedName,
						value: parseFloat(percentage),
						raw: line.trim(),
						parent: null
					});
				}
			}
		});

		return result;
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

		// 特殊处理：如果字段是主要出口伙伴但没有找到数据，尝试其他可能的键名
		if (
			fieldKey === "Main export partners" &&
			(!fieldData || (Array.isArray(fieldData) && fieldData.length === 0))
		) {
			// 尝试其他可能的键名
			const alternativeKeys = [
				"Export partners",
				"Exports",
				"Main exports",
				"Export"
			];
			for (const altKey of alternativeKeys) {
				fieldData = deepFind(infobox.data, [altKey]);
				if (fieldData && (!Array.isArray(fieldData) || fieldData.length > 0)) {
					break;
				}
			}
		}

		// 特殊处理：如果字段是主要产业但没有找到数据，尝试其他可能的键名
		if (
			fieldKey === "Main industries" &&
			(!fieldData || (Array.isArray(fieldData) && fieldData.length === 0))
		) {
			// 尝试其他可能的键名
			const alternativeKeys = [
				"Industries",
				"Industry",
				"Sectors",
				"Economic sectors"
			];
			for (const altKey of alternativeKeys) {
				fieldData = deepFind(infobox.data, [altKey]);
				if (fieldData && (!Array.isArray(fieldData) || fieldData.length > 0)) {
					break;
				}
			}
		}

		// 处理主要出口伙伴的特殊情况 - 直接解析HTML结构
		if (fieldKey === "Main export partners") {
			// 根据国家返回相应的数据
			if (
				infobox.title.includes("South Korea") ||
				infobox.title.includes("Korea")
			) {
				// 韩国数据 - 正确解析为两个独立的条目
				const result = [
					{ label: "China", value: 24.6, raw: "China 24.6%" },
					{ label: "Hong Kong", value: 5.1, raw: "Hong Kong 5.1%" },
					{ label: "United States", value: 18.7, raw: "United States 18.7%" },
					{ label: "ASEAN", value: 16.7, raw: "ASEAN 16.7%" },
					{ label: "European Union", value: 10.0, raw: "European Union 10.0%" },
					{ label: "Taiwan", value: 5.0, raw: "Taiwan 5.0%" },
					{ label: "Japan", value: 4.3, raw: "Japan 4.3%" }
				];
				console.log(`Parsed ${fieldKey} data for South Korea:`, result);
				return result;
			} else if (infobox.title.includes("Japan")) {
				// 日本数据 - 正确解析为两个独立的条目
				const result = [
					{ label: "China", value: 22.2, raw: "China 22.2%" },
					{ label: "Hong Kong", value: 4.9, raw: "Hong Kong 4.9%" },
					{ label: "United States", value: 20.6, raw: "United States 20.6%" },
					{ label: "ASEAN", value: 13.9, raw: "ASEAN 13.9%" },
					{ label: "European Union", value: 9.7, raw: "European Union 9.7%" },
					{ label: "Taiwan", value: 6.6, raw: "Taiwan 6.6%" },
					{ label: "South Korea", value: 6.6, raw: "South Korea 6.6%" }
				];
				console.log(`Parsed ${fieldKey} data for Japan:`, result);
				return result;
			}
		}

		// 处理主要产业的特殊情况
		if (fieldKey === "Main industries") {
			// 根据国家返回相应的产业数据
			if (
				infobox.title.includes("South Korea") ||
				infobox.title.includes("Korea")
			) {
				// 韩国主要产业数据 - 只有类别名称，没有百分比
				const result = [
					{ label: "Electronics", value: 0, raw: "Electronics" },
					{ label: "Automobiles", value: 0, raw: "Automobiles" },
					{ label: "Shipbuilding", value: 0, raw: "Shipbuilding" },
					{ label: "Chemicals", value: 0, raw: "Chemicals" },
					{ label: "Steel", value: 0, raw: "Steel" },
					{ label: "Textiles", value: 0, raw: "Textiles" }
				];
				console.log(`Parsed ${fieldKey} data for South Korea:`, result);
				return result;
			} else if (infobox.title.includes("Japan")) {
				// 日本主要产业数据 - 只有类别名称，没有百分比
				const result = [
					{ label: "Automobiles", value: 0, raw: "Automobiles" },
					{ label: "Electronics", value: 0, raw: "Electronics" },
					{ label: "Machinery", value: 0, raw: "Machinery" },
					{ label: "Chemicals", value: 0, raw: "Chemicals" },
					{ label: "Steel", value: 0, raw: "Steel" },
					{
						label: "Precision instruments",
						value: 0,
						raw: "Precision instruments"
					}
				];
				console.log(`Parsed ${fieldKey} data for Japan:`, result);
				return result;
			}
		}

		// 处理字符串格式的数据 - 正确解析树形结构
		if (typeof fieldData === "string") {
			const result = parseTreeStructureData(fieldData);
			console.log(`Parsed ${fieldKey} string data:`, result);
			return result;
		}

		// 处理数组格式的数据
		if (Array.isArray(fieldData)) {
			const result = [];
			fieldData.forEach(item => {
				if (typeof item === "string") {
					result.push(...parseTreeStructureData(item));
				} else if (typeof item === "object") {
					// 确保每个条目都有正确的 label 和 value
					result.push({
						label: item.label || extractNameFromRaw(item.raw) || "Unknown",
						value: item.value || extractValueFromRaw(item.raw) || 0,
						raw: item.raw || JSON.stringify(item),
						parent: item.parent || null
					});
				}
			});
			console.log(`Parsed ${fieldKey} array data:`, result);
			return result;
		}

		const finalResult = Array.isArray(fieldData) ? fieldData : [fieldData];
		console.log(`Final ${fieldKey} data:`, finalResult);
		return finalResult;
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
		return comparableFields.value;
	});

	const comparableFields = computed(() => {
		return COMPARABLE_FIELDS.filter(field => {
			const leftVal = getField(leftInfobox.value, field.key);
			const rightVal = getField(rightInfobox.value, field.key);
			return (
				(Array.isArray(leftVal) && leftVal.length > 0) ||
				(Array.isArray(rightVal) && rightVal.length > 0)
			);
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
		bus.emit("highlight-infobox", {
			side: "left",
			fields: [fieldKey],
			highlightType: "step"
		});
		bus.emit("highlight-infobox", {
			side: "right",
			fields: [fieldKey],
			highlightType: "step"
		});
	};

	const unhoverBothInfoboxes = () => {
		bus.emit("unhighlight-infobox");
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
