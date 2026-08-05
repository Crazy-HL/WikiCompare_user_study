<template>
	<div class="full-chart">
		<div
			v-if="adaptiveTriggered"
			class="scale-mode-switch"
			role="group"
			aria-label="图表刻度模式">
			<button
				v-for="option in scaleModeOptions"
				:key="option.value"
				type="button"
				:class="{ active: selectedScaleMode === option.value }"
				:disabled="option.value === 'index' && !canUseTrendIndex"
				@click="selectedScaleMode = option.value">
				{{ option.label }}
			</button>
		</div>
		<div
			v-if="adaptiveTriggered && chartVisualization === 'line-chart'"
			class="scale-mode-note">
			{{ fullTrendText }}
		</div>
		<div v-if="isTextMode" class="full-text">
			<div v-for="(item, index) in textRows" :key="index" class="text-item">
				<span class="text-label">{{ item.label }}</span>
				<span class="text-value">{{ item.value }}</span>
			</div>
		</div>
		<div v-else-if="hasNumericData" ref="chartEl" class="chart-container"></div>
		<div v-else class="no-data">无可用数据</div>
	</div>
</template>

<script setup>
	import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
	import * as echarts from "echarts";
	const {
		formatChartNumber,
		pieLegendLabelForPoint,
		shortValueText
	} = require("@/js/chartValueDisplay");
	const {
		CHART_COLORS,
		CHART_REMAINDER_COLOR,
		PAPER_PIE_COLORS,
		categoryColor,
		colorFromMap
	} = require("@/js/chartTheme");
	const {
		trendChange,
		trendIndexPoints
	} = require("@/js/adaptiveChartScale");
	const {
		buildFullChartBarOption,
		buildFullChartLineOption,
		canonicalAdaptiveContextEnabled,
		linearScaleDecision,
		orderedLinePoints,
		plotDataForContext
	} = require("@/js/fullChartAdaptiveOptions");

	const props = defineProps({
		field: [Object, Array, String, Number],
		type: String,
		visualization: String,
		fieldKey: String,
		side: {
			type: String,
			default: ""
		},
		scaleContext: {
			type: Object,
			default: null
		},
		categoryColors: {
			type: Object,
			default: () => ({})
		}
	});

	const chartEl = ref(null);
	let chart = null;
	let renderScheduleToken = 0;
	let renderLayoutFrameId = null;
	let renderFrameId = null;
	let renderTimeoutId = null;

	const COLORS = CHART_COLORS;
	const PIE_COLORS = PAPER_PIE_COLORS;
	const REMAINDER_COLOR = CHART_REMAINDER_COLOR;
	const pieColorFor = (name, index) =>
		colorFromMap(props.categoryColors, name) || PIE_COLORS[index % PIE_COLORS.length];
	const pieSliceStyle = (color, opacity = 0.92) => ({
		color,
		borderColor: "#ffffff",
		borderWidth: 2,
		opacity
	});
	const selectedScaleMode = ref("auto");
	const scaleModeOptions = [
		{ value: "auto", label: "自动优化" },
		{ value: "linear", label: "原始线性" },
		{ value: "index", label: "趋势指数" }
	];
	const scaleDecision = ref(linearScaleDecision());
	const hasCanonicalScaleContext = computed(() =>
		canonicalAdaptiveContextEnabled({
			scaleContext: props.scaleContext,
			side: props.side,
			visualization: chartVisualization.value,
			dataLength: numericData.value.length
		})
	);
	const plotData = computed(() =>
		plotDataForContext({
			data: numericData.value,
			scaleContext: props.scaleContext,
			side: props.side,
			visualization: chartVisualization.value
		})
	);
	const adaptiveTriggered = computed(
		() =>
			hasCanonicalScaleContext.value &&
			plotData.value.length > 0 &&
			["log", "symlog"].includes(scaleDecision.value.mode)
	);
	const canUseTrendIndex = computed(
		() =>
			chartVisualization.value === "line-chart" &&
			trendIndexPoints(orderedLinePoints(plotData.value)).length > 0
	);
	const fullTrendText = computed(() => {
		const change = trendChange(plotData.value);
		if (change.absoluteChange === null) return "";
		if (change.percentChange === null) {
			return `首值为 0，绝对变化 ${formatChartNumber(
				change.absoluteChange,
				axisType.value
			)}`;
		}
		const sign = change.percentChange > 0 ? "+" : "";
		return `${change.firstYear || "起点"} 至 ${change.lastYear || "终点"}：${sign}${change.percentChange.toFixed(1)}%`;
	});

	const isYearEntry = value => {
		if (typeof value !== "string") return false;
		const trimmed = value.trim();
		return /^\(\d{4}.*\)$/.test(trimmed) || /^\d{4}$/.test(trimmed);
	};

	const numericValue = value => {
		if (value === null || value === undefined || value === "") return null;
		if (typeof value === "number") return Number.isFinite(value) ? value : null;
		if (typeof value === "object") return numericValue(value.value ?? value.raw);
		const source = String(value)
			.replace(/\u00a0/g, " ")
			.replace(/US\$|[$¥₩€£,%]/g, "")
			.trim();
		const number = parseFloat(source.replace(/,/g, ""));
		if (!Number.isFinite(number)) return null;
		const lower = source.toLowerCase();
		if (lower.includes("trillion")) return number * 1e12;
		if (lower.includes("billion")) return number * 1e9;
		if (lower.includes("million")) return number * 1e6;
		if (lower.includes("thousand")) return number * 1e3;
		return number;
	};

	const cleanLabel = (value, fallback = "项目") => {
		const text = String(value || "")
			.replace(/\u00a0/g, " ")
			.replace(/\s+/g, " ")
			.trim();
		return text || fallback;
	};

	const shortValueDisplay = item => {
		return shortValueText(item, axisType.value);
	};

	const normalizedData = computed(() => {
		if (!props.field || props.field === "-") return [];
		const values = Array.isArray(props.field) ? props.field : [props.field];
		return values
			.map((item, index) => {
				if (typeof item === "object" && item !== null) {
					const raw = cleanLabel(
						item.raw ?? item.display ?? item.label ?? item.value,
						""
					);
					const originalDisplay = cleanLabel(
						item.originalDisplay ?? item.display ?? item.raw ?? item.value,
						raw || "-"
					);
					const display = cleanLabel(
						item.display ?? item.originalDisplay ?? item.raw ?? item.value,
						originalDisplay
					);
					const label = cleanLabel(item.label ?? item.year ?? raw, `项目${index + 1}`);
					return {
						value: numericValue(item.value ?? item.raw),
						raw,
						display,
						originalDisplay,
						label,
						year: item.year ?? null,
						parent: item.parent ?? null,
						unit: item.unit ?? null
					};
				}
				const raw = cleanLabel(item, "");
				return {
					value: numericValue(item),
					raw,
					display: raw || "-",
					originalDisplay: raw || "-",
					label: raw || `项目${index + 1}`,
					year: null,
					parent: null,
					unit: null
				};
			})
			.filter(item => item.display && !isYearEntry(item.raw));
	});

	const numericData = computed(() =>
		normalizedData.value.filter(item => Number.isFinite(item.value))
	);

	const hasNumericData = computed(() => numericData.value.length > 0);

	const isTextMode = computed(
		() => props.visualization === "text-only" || !chartVisualization.value
	);

	const chartVisualization = computed(() => {
		if (props.visualization === "text-only") return "";
		if (props.visualization === "pie-chart") {
			return usablePieData.value.length ? "pie-chart" : "bar-chart";
		}
		if (
			["bar-chart", "line-chart", "stacked-chart"].includes(props.visualization)
		) {
			return props.visualization;
		}
		return "";
	});

	const textRows = computed(() => {
		const rows = normalizedData.value.length
			? normalizedData.value
			: [{ label: props.fieldKey || "值", display: String(props.field || "-") }];
		return rows.map((item, index) => ({
			label: item.label || `${props.fieldKey || "值"} ${index + 1}`,
			value: item.display || item.raw || "-"
		}));
	});

	const usablePieData = computed(() => {
		const data = numericData.value.filter(item => item.value > 0);
		if (data.length > 1) return data;
		if (data.length === 1 && isPercentageType.value && data[0].value <= 100) {
			return data;
		}
		return [];
	});

	const isPercentageType = computed(() => {
		const type = String(props.type || "").toLowerCase();
		return type === "percentage" || type === "proportional";
	});

	const resize = () => scheduleRenderChart();

	const disposeChart = () => {
		chart?.dispose();
		chart = null;
	};

	const clearScheduledRender = () => {
		if (
			renderLayoutFrameId !== null &&
			typeof window !== "undefined" &&
			typeof window.cancelAnimationFrame === "function"
		) {
			window.cancelAnimationFrame(renderLayoutFrameId);
		}
		if (
			renderFrameId !== null &&
			typeof window !== "undefined" &&
			typeof window.cancelAnimationFrame === "function"
		) {
			window.cancelAnimationFrame(renderFrameId);
		}
		if (renderTimeoutId !== null) {
			clearTimeout(renderTimeoutId);
		}
		renderLayoutFrameId = null;
		renderFrameId = null;
		renderTimeoutId = null;
	};

	const cancelScheduledRender = () => {
		renderScheduleToken += 1;
		clearScheduledRender();
	};

	const scheduleRenderChart = () => {
		const token = ++renderScheduleToken;
		clearScheduledRender();
		nextTick(() => {
			if (token !== renderScheduleToken) return;
			const render = () => {
				if (token !== renderScheduleToken) return;
				renderFrameId = null;
				renderTimeoutId = null;
				renderChart();
			};
			if (
				typeof window !== "undefined" &&
				typeof window.requestAnimationFrame === "function"
			) {
				renderLayoutFrameId = window.requestAnimationFrame(() => {
					renderLayoutFrameId = null;
					if (token !== renderScheduleToken) return;
					renderFrameId = window.requestAnimationFrame(render);
				});
				return;
			}
			renderTimeoutId = setTimeout(render, 0);
		});
	};

	const renderChart = () => {
		if (isTextMode.value || !hasNumericData.value || !chartEl.value) {
			scaleDecision.value = linearScaleDecision();
			disposeChart();
			return;
		}
		if (!chart) chart = echarts.init(chartEl.value);
		else chart.resize();
		chart.setOption(buildOption(), true);
	};

	const buildOption = () => {
		if (chartVisualization.value === "line-chart") return lineOption();
		if (chartVisualization.value === "pie-chart") return pieOption();
		if (chartVisualization.value === "stacked-chart") return stackedOption();
		return barOption();
	};

	const adaptiveOptionArgs = visualization => ({
		data: numericData.value,
		scaleContext: chartVisualization.value === visualization ? props.scaleContext : null,
		side: props.side,
		selectedScaleMode: selectedScaleMode.value,
		chartHeight: chartEl.value?.clientHeight || 0,
		fieldKey: props.fieldKey,
		axisType: axisType.value,
		axisUnitLabel: axisUnitLabel.value,
		colors: COLORS
	});

	const barOption = () => {
		const result = buildFullChartBarOption(adaptiveOptionArgs("bar-chart"));
		scaleDecision.value = result.state.decision;
		return result.option;
	};

	const lineOption = () => {
		const result = buildFullChartLineOption(adaptiveOptionArgs("line-chart"));
		scaleDecision.value = result.state.decision;
		return result.option;
	};

	const pieOption = () => {
		const data = usablePieData.value;
		const isSingle = data.length === 1;
		const pieCategoryLabel = (item, index) =>
			pieLegendLabelForPoint(item, index, {
				fallback: props.fieldKey,
				total: data.length
			});
		const seriesData = isSingle
			? [
					{
						name: pieCategoryLabel(data[0], 0),
						value: Math.max(0, Math.min(100, data[0].value)),
						display: data[0].display,
						shortDisplay: shortValueDisplay(data[0]),
						itemStyle: pieSliceStyle(pieColorFor(pieCategoryLabel(data[0], 0), 0))
					},
					{
						name: "剩余",
						value: Math.max(0, 100 - Math.max(0, Math.min(100, data[0].value))),
						display: "剩余",
						silent: true,
						label: { show: false },
						itemStyle: pieSliceStyle(REMAINDER_COLOR, 0.5)
					}
			  ]
			: data.map((item, index) => {
					const categoryLabel = pieCategoryLabel(item, index);
					return {
						name: categoryLabel,
						value: item.value,
						display: item.display,
						shortDisplay: shortValueDisplay(item),
						itemStyle: pieSliceStyle(pieColorFor(categoryLabel, index))
					};
			  });
		return {
			tooltip: {
				trigger: "item",
				formatter: params =>
					params.data?.silent
						? ""
						: `${params.marker}${params.name}: ${params.data?.display || params.value}`
			},
			legend: {
				type: "scroll",
				orient: "horizontal",
				left: "center",
				bottom: 0,
				icon: "circle",
				itemWidth: 10,
				itemHeight: 10,
				textStyle: { color: "#334155", fontSize: 12 }
			},
			series: [
				{
					type: "pie",
					radius: isSingle ? ["44%", "68%"] : ["0%", "68%"],
					center: ["50%", "44%"],
					data: seriesData,
					minAngle: 2,
					avoidLabelOverlap: true,
					label: {
						color: "#1f2937",
						fontSize: 11,
						formatter: params => {
							if (params.data?.silent) return "";
							return isSingle
								? params.data?.shortDisplay || params.data?.display || "-"
								: params.data?.shortDisplay || params.data?.display || "-";
						}
					},
					labelLine: { length: 14, length2: 8 }
				}
			]
		};
	};

		const stackedOption = () => {
			const data = numericData.value.filter(item => item.value > 0);
			const total = data.reduce((sum, item) => sum + item.value, 0);
			if (!data.length || total <= 0) return barOption();
			const renderTotal = total > 101 ? total : 100;
			const legendNames = data.map(item => item.label);
			const splitIndex = Math.ceil(legendNames.length / 2);
			const chartWidth = chartEl.value?.clientWidth || 760;
			const sideInset = chartWidth < 640 ? 104 : 148;
			const legendFormatter = name =>
				name.length > (chartWidth < 640 ? 12 : 18)
					? `${name.slice(0, chartWidth < 640 ? 11 : 17)}…`
					: name;
			return {
				color: COLORS,
				tooltip: {
					trigger: "item",
					formatter: params =>
						`${params.marker}${params.seriesName}: ${
							params.data?.display ||
								formatChartNumber(params.data?.originalValue, axisType.value)
						}`
				},
				legend: [
					{
						type: "scroll",
						orient: "vertical",
						left: 8,
						top: "middle",
						data: legendNames.slice(0, splitIndex),
						icon: "roundRect",
						itemWidth: 14,
						itemHeight: 8,
						itemGap: 10,
						selectedMode: false,
						formatter: legendFormatter,
						textStyle: { color: "#334155", fontSize: 12, width: sideInset - 34 },
						pageIconColor: "#64748b",
						pageIconInactiveColor: "#cbd5e1",
						pageTextStyle: { color: "#64748b" }
					},
					{
						type: "scroll",
						orient: "vertical",
						right: 8,
						top: "middle",
						data: legendNames.slice(splitIndex),
						icon: "roundRect",
						itemWidth: 14,
						itemHeight: 8,
						itemGap: 10,
						selectedMode: false,
						formatter: legendFormatter,
						textStyle: { color: "#334155", fontSize: 12, width: sideInset - 34 },
						pageIconColor: "#64748b",
						pageIconInactiveColor: "#cbd5e1",
						pageTextStyle: { color: "#64748b" }
					}
				],
				grid: {
					top: 34,
					left: sideInset,
					right: sideInset,
					bottom: 42,
					containLabel: true
				},
				xAxis: {
					type: "category",
					data: [props.fieldKey || "Composition"],
					axisTick: { show: false },
					axisLine: { lineStyle: { color: "#cbd5e1" } },
					axisLabel: {
						color: "#475569",
						fontSize: 12,
						overflow: "truncate",
						width: 120
					}
				},
				yAxis: {
					type: "value",
					min: 0,
					max: 100,
					axisLabel: {
						color: "#475569",
						formatter: value => `${value}%`
					},
					axisLine: { show: false },
					splitLine: { lineStyle: { color: "#e5eaf1" } }
				},
				series: data.map((item, index) => {
					const renderValue = (item.value / renderTotal) * 100;
					return {
						name: item.label,
						type: "bar",
						stack: "total",
						barWidth: 46,
						data: [
							{
								value: renderValue,
								originalValue: item.value,
								display: item.display,
								shortDisplay: shortValueDisplay(item)
							}
						],
						itemStyle: {
							color: categoryColor(item.label, index, props.categoryColors),
							borderRadius:
								index === 0
									? [0, 0, 4, 4]
									: index === data.length - 1
										? [4, 4, 0, 0]
										: 0
						},
						label: {
							show: renderValue >= 12,
							position: "inside",
							color: "#111827",
							fontSize: 11,
							formatter: params => params.data?.shortDisplay || ""
						}
					};
				})
			};
		};

	const axisType = computed(() =>
		isPercentageType.value ? "percentage" : String(props.type || "")
	);

	const axisUnitLabel = computed(() => {
		if (axisType.value === "percentage") return "";
		const source = [
			props.fieldKey,
			...normalizedData.value.flatMap(item => [item.raw, item.display, item.unit])
		]
			.filter(Boolean)
			.join(" ");
		if (/liters?\s+of\s+pure\s+alcohol/i.test(source)) {
			return /per\s+capita/i.test(source)
				? "liters of pure alcohol per capita"
				: "liters of pure alcohol";
		}
		return "";
	});

	onMounted(() => {
		scheduleRenderChart();
		window.addEventListener("resize", resize);
	});

	watch(
		() => [
			props.field,
			props.type,
			props.visualization,
			props.fieldKey,
			props.side,
			props.scaleContext,
			selectedScaleMode.value
		],
		() => {
			if (!plotData.value.length) scaleDecision.value = linearScaleDecision();
			scheduleRenderChart();
		},
		{ deep: true }
	);

	watch(
		() => props.scaleContext,
		() => {
			selectedScaleMode.value = "auto";
			scaleDecision.value = linearScaleDecision();
		},
		{ deep: true }
	);

	onUnmounted(() => {
		window.removeEventListener("resize", resize);
		cancelScheduledRender();
		disposeChart();
	});
</script>

<style scoped>
	.full-chart {
		width: 100%;
		height: 100%;
		min-height: 420px;
		box-sizing: border-box;
		color: #1f2937;
	}

	.scale-mode-switch {
		display: flex;
		justify-content: center;
		gap: 6px;
		margin-bottom: 8px;
	}

	.scale-mode-switch button {
		border: 1px solid #cbd5e1;
		border-radius: 999px;
		background: #ffffff;
		padding: 5px 11px;
		color: #475569;
		cursor: pointer;
		font-size: 12px;
		font-weight: 600;
	}

	.scale-mode-switch button.active {
		border-color: #2563eb;
		background: #eff6ff;
		color: #1d4ed8;
	}

	.scale-mode-switch button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}

	.scale-mode-note {
		margin: -2px 0 8px;
		color: #64748b;
		font-size: 12px;
		text-align: center;
	}

	.chart-container {
		width: 100%;
		height: 100%;
		min-height: 420px;
		border: 1px solid #dbe3ee;
		border-radius: 8px;
		background:
			linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
	}

	.full-text {
		display: grid;
		gap: 8px;
		max-height: 440px;
		overflow-y: auto;
	}

	.text-item {
		display: grid;
		grid-template-columns: minmax(120px, 0.32fr) minmax(0, 1fr);
		gap: 10px;
		padding: 9px 11px;
		border: 1px solid #dbe3ee;
		border-radius: 6px;
		background: #fbfdff;
		line-height: 1.45;
	}

	.text-label {
		color: #64748b;
		font-size: 12px;
		font-weight: 600;
		overflow-wrap: anywhere;
	}

	.text-value {
		font-size: 13px;
		overflow-wrap: anywhere;
		white-space: pre-wrap;
	}

	.no-data {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 420px;
		border: 1px solid #dbe3ee;
		border-radius: 8px;
		background: #fbfdff;
		color: #64748b;
		font-size: 14px;
	}

	@media (max-width: 760px) {
		.text-item {
			grid-template-columns: 1fr;
		}
	}
</style>
