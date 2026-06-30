<template>
	<div class="full-chart">
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
		barChartDomain,
		formatChartNumber,
		xLabelForPoint
	} = require("@/js/chartValueDisplay");

	const props = defineProps({
		field: [Object, Array, String, Number],
		type: String,
		visualization: String,
		fieldKey: String
	});

	const chartEl = ref(null);
	let chart = null;

	const COLORS = [
		"#3867a8",
		"#c94f45",
		"#5f8f3f",
		"#d9902f",
		"#7d5fb2",
		"#2f8c8f",
		"#b05f6d",
		"#6b7280"
	];
	const REMAINDER_COLOR = "#e7edf4";

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
		const display = String(item?.display || "").trim();
		const colonIndex = display.lastIndexOf(":");
		if (colonIndex >= 0) return display.slice(colonIndex + 1).trim();
		return display || formatAxisValue(item?.value);
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
					const display = cleanLabel(
						item.display ?? item.raw ?? item.value,
						raw || "-"
					);
					const label = cleanLabel(item.label ?? item.year ?? raw, `项目${index + 1}`);
					return {
						value: numericValue(item.value ?? item.raw),
						raw,
						display,
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

	const resize = () => chart?.resize();

	const disposeChart = () => {
		chart?.dispose();
		chart = null;
	};

	const renderChart = () => {
		if (isTextMode.value || !hasNumericData.value || !chartEl.value) {
			disposeChart();
			return;
		}
		if (!chart) chart = echarts.init(chartEl.value);
		chart.setOption(buildOption(), true);
	};

	const buildOption = () => {
		if (chartVisualization.value === "line-chart") return lineOption();
		if (chartVisualization.value === "pie-chart") return pieOption();
		if (chartVisualization.value === "stacked-chart") return stackedOption();
		return barOption();
	};

	const baseTooltip = formatter => ({
		trigger: "axis",
		axisPointer: { type: "shadow" },
		formatter
	});

	const baseGrid = (bottom = 48) => ({
		top: 34,
		left: 60,
		right: 28,
		bottom,
		containLabel: true
	});

	const barOption = () => {
		const data = numericData.value;
		const values = data.map(item => item.value);
		const [min, max] = barChartDomain(values);
		return {
			color: COLORS,
			tooltip: baseTooltip(params =>
				params
					.map(param => `${param.marker}${param.name}: ${param.data.display}`)
					.join("<br/>")
			),
			grid: baseGrid(data.length > 5 ? 76 : 48),
			xAxis: {
				type: "category",
				data: data.map((item, index) => xLabelForPoint(item, index)),
				axisTick: { alignWithLabel: true },
				axisLine: { lineStyle: { color: "#cbd5e1" } },
				axisLabel: {
					interval: 0,
					rotate: data.length > 5 ? 28 : 0,
					color: "#475569",
					fontSize: 11,
					overflow: "truncate",
					width: 90
				}
			},
			yAxis: {
				type: "value",
				min,
				max,
				axisLabel: {
					color: "#475569",
					formatter: value => formatAxisValue(value)
				},
				axisLine: { show: false },
				splitLine: { lineStyle: { color: "#e5eaf1" } }
			},
			series: [
				{
					type: "bar",
					barMaxWidth: 54,
					data: data.map((item, index) => ({
						value: item.value,
						display: item.display,
						shortDisplay: shortValueDisplay(item),
						itemStyle: {
							color: COLORS[index % COLORS.length],
							borderRadius:
								item.value >= 0 ? [4, 4, 0, 0] : [0, 0, 4, 4]
						}
					})),
					label: {
						show: true,
						position: "top",
						color: "#1f2937",
						fontSize: 11,
						formatter: params =>
							params.data?.shortDisplay || params.data?.display || "-"
					},
					markLine:
						min < 0 && max > 0
							? {
									silent: true,
									symbol: "none",
									lineStyle: { color: "#94a3b8", type: "dashed", width: 1 },
									data: [{ yAxis: 0 }]
							  }
							: undefined
				}
			],
			dataZoom:
				data.length > 10
					? [
							{
								type: "slider",
								height: 18,
								bottom: 14,
								start: 0,
								end: Math.min(100, (10 / data.length) * 100)
							}
					  ]
					: []
		};
	};

	const lineOption = () => {
		const data = [...numericData.value].sort((a, b) => {
			const left = Number(a.year);
			const right = Number(b.year);
			if (Number.isFinite(left) && Number.isFinite(right)) return left - right;
			return 0;
		});
		const values = data.map(item => item.value);
		const [min, max] = paddedDomain(values);
		return {
			color: [COLORS[0]],
			tooltip: {
				trigger: "axis",
				formatter: params =>
					params
						.map(param => `${param.marker}${param.name}: ${param.data.display}`)
						.join("<br/>")
			},
			grid: baseGrid(data.length > 6 ? 72 : 48),
			xAxis: {
				type: "category",
				boundaryGap: false,
				data: data.map((item, index) => xLabelForPoint(item, index)),
				axisLabel: {
					interval: 0,
					rotate: data.length > 6 ? 24 : 0,
					color: "#475569",
					fontSize: 11
				},
				axisLine: { lineStyle: { color: "#cbd5e1" } }
			},
			yAxis: {
				type: "value",
				min,
				max,
				axisLabel: {
					color: "#475569",
					formatter: value => formatAxisValue(value)
				},
				axisLine: { show: false },
				splitLine: { lineStyle: { color: "#e5eaf1" } }
			},
			series: [
				{
					type: "line",
					smooth: false,
					symbol: "circle",
					symbolSize: 8,
					data: data.map(item => ({
						value: item.value,
						display: item.display,
						shortDisplay: shortValueDisplay(item)
					})),
					lineStyle: { width: 2.5 },
					label: {
						show: data.length <= 8,
						position: "top",
						color: "#1f2937",
						fontSize: 11,
						formatter: params =>
							params.data?.shortDisplay || params.data?.display || "-"
					}
				}
			],
			dataZoom:
				data.length > 12
					? [
							{
								type: "slider",
								height: 18,
								bottom: 14,
								start: 0,
								end: Math.min(100, (12 / data.length) * 100)
							}
					  ]
					: []
		};
	};

	const pieOption = () => {
		const data = usablePieData.value;
		const isSingle = data.length === 1;
		const seriesData = isSingle
			? [
					{
						name: data[0].label,
						value: Math.max(0, Math.min(100, data[0].value)),
						display: data[0].display,
						shortDisplay: shortValueDisplay(data[0]),
						itemStyle: { color: COLORS[0] }
					},
					{
						name: "剩余",
						value: Math.max(0, 100 - Math.max(0, Math.min(100, data[0].value))),
						display: "剩余",
						silent: true,
						label: { show: false },
						itemStyle: { color: REMAINDER_COLOR }
					}
			  ]
			: data.map((item, index) => ({
					name: item.label,
					value: item.value,
					display: item.display,
					shortDisplay: shortValueDisplay(item),
					itemStyle: { color: COLORS[index % COLORS.length] }
			  }));
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
				icon: "roundRect",
				itemWidth: 14,
				itemHeight: 8,
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
								: `${params.name}\n${params.data?.shortDisplay || params.value}`;
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
							params.data?.display || formatAxisValue(params.data?.originalValue)
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
							color: COLORS[index % COLORS.length],
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

	const paddedDomain = values => {
		const nums = values.filter(Number.isFinite);
		if (!nums.length) return [0, 1];
		const min = Math.min(...nums);
		const max = Math.max(...nums);
		if (min === max) {
			const padding = Math.max(1, Math.abs(min) * 0.12);
			return [min - padding, max + padding];
		}
		const padding = (max - min) * 0.12;
		return [min - padding, max + padding];
	};

	const formatAxisValue = value => formatChartNumber(value, axisType.value);

	const axisType = computed(() =>
		isPercentageType.value ? "percentage" : String(props.type || "")
	);

	onMounted(() => {
		nextTick(renderChart);
		window.addEventListener("resize", resize);
	});

	watch(
		() => [props.field, props.type, props.visualization, props.fieldKey],
		() => nextTick(renderChart),
		{ deep: true }
	);

	onUnmounted(() => {
		window.removeEventListener("resize", resize);
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
