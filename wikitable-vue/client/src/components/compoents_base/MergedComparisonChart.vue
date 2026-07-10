<template>
	<div class="merged-comparison">
		<div v-if="emptyMergedChart" class="merged-empty">无可合并图表数据</div>
		<div v-else ref="chartEl" class="merged-chart"></div>
	</div>
</template>

<script setup>
	import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
	import * as echarts from "echarts";
	const { buildMergedComparison } = require("@/js/mergedComparisonData");
	const { formatAxisNumber } = require("@/js/chartValueDisplay");
	const {
		CHART_COLORS,
		CHART_LINE_WIDTH,
		categoryColor
	} = require("@/js/chartTheme");

	const props = defineProps({
		row: {
			type: Object,
			required: true
		},
		titles: {
			type: Object,
			default: () => ({})
		}
	});

	const chartEl = ref(null);
	let chart = null;
	const AXIS_SPLIT_NUMBER = 4;

	const merged = computed(() => buildMergedComparison(props.row, props.titles));
	const emptyMergedChart = computed(() => {
		const data = merged.value;
		return (
			data.mode === "text" ||
			!data.series?.some(series =>
				series.data?.some(point => Number.isFinite(Number(point.value)))
			)
		);
	});

	const resize = () => chart?.resize();

	const renderChart = () => {
		if (emptyMergedChart.value) {
			chart?.dispose();
			chart = null;
			return;
		}
		if (!chartEl.value) return;
		if (!chart) chart = echarts.init(chartEl.value);
		chart.setOption(chartOption(merged.value), true);
	};

	const chartOption = data => {
		const isLine = data.mode === "line";
		const isSingle = data.mode === "single";
		const isStacked = data.mode === "stacked";
		const colors = [CHART_COLORS[0], CHART_COLORS[1]];
		const series = isStacked ? stackedSeries(data) : standardSeries(data, colors, isLine, isSingle);

		return {
			color: isStacked
				? data.categories.map((category, index) => categoryColor(category, index))
				: colors,
			tooltip: {
				trigger: "axis",
				axisPointer: { type: isLine ? "line" : "shadow" },
				formatter: params =>
					params
						.map(param => {
							const display = param.data?.display || "-";
							return `${param.marker}${param.seriesName}: ${display}`;
						})
						.join("<br/>")
			},
			legend: {
				top: 0,
				left: "center",
				icon: "roundRect",
				itemWidth: 14,
				itemHeight: 8,
				textStyle: { color: "#334155", fontSize: 12 }
			},
			grid: {
				top: 48,
				left: 56,
				right: 28,
				bottom: data.categories.length > 4 && !isStacked ? 70 : 42,
				containLabel: true
			},
			xAxis: {
				type: "category",
				data: isStacked ? data.series.map(item => item.name) : data.categories,
				axisTick: { alignWithLabel: true },
				axisLabel: {
					interval: 0,
					rotate: data.categories.length > 4 && !isStacked ? 24 : 0,
					color: "#475569",
					fontSize: 11,
					hideOverlap: true
				},
				axisLine: { lineStyle: { color: "#cbd5e1" } }
			},
			yAxis: {
				type: "value",
				min: isStacked ? 0 : data.yDomain[0],
				max: isStacked ? 100 : data.yDomain[1],
				splitNumber: AXIS_SPLIT_NUMBER,
				name: axisMeasureLabel(data),
				nameLocation: "middle",
				nameGap: 42,
				nameTextStyle: {
					color: "#475569",
					fontSize: 11,
					fontWeight: 600
				},
				axisLabel: {
					color: "#475569",
					formatter: value => isStacked ? `${value}%` : formatAxis(value, data)
				},
				splitLine: { lineStyle: { color: "#e5eaf1" } },
				axisLine: { show: false }
			},
			series,
			dataZoom: []
		};
	};

	const standardSeries = (data, colors, isLine, isSingle) => data.series.map((item, index) => ({
		name: item.name,
		type: isLine ? "line" : "bar",
		smooth: false,
		symbol: isLine ? "circle" : "none",
		symbolSize: 8,
		barMaxWidth: isSingle ? 42 : 28,
		barGap: "14%",
		data: item.data.map(point => ({
			value: point.value,
			display: point.display,
			raw: point.raw
		})),
		label: {
			show: shouldShowPointLabels(data, isLine),
			position: pointLabelPosition(data, item),
			distance: 8,
			color: "#243447",
			fontSize: 11,
			formatter: params => params.data?.display || "-"
		},
		lineStyle: { width: CHART_LINE_WIDTH },
		itemStyle: {
			color: colors[index % colors.length],
			borderRadius: isLine ? 0 : [4, 4, 0, 0]
		}
	}));

	const shouldShowPointLabels = (data, isLine) => {
		if (!isLine) return true;
		return (data.categories || []).length <= 16;
	};

	const stackedSeries = data => data.categories.map((category, categoryIndex) => ({
		name: category,
		type: "bar",
		stack: "total",
		barMaxWidth: 72,
		data: data.series.map(side => {
			const point = side.data[categoryIndex] || {};
			const total = side.data.reduce((sum, item) => (
				Number.isFinite(item.value) && item.value > 0 ? sum + item.value : sum
			), 0);
			const renderTotal = total > 101 ? total : 100;
			const percent = renderTotal && Number.isFinite(point.value) && point.value > 0
				? (point.value / renderTotal) * 100
				: null;
			return {
				value: percent,
				display: point.display,
				raw: point.raw
			};
		}),
		label: {
			show: false
		},
		emphasis: {
			focus: "series"
		}
	}));

	const pointLabelPosition = (data, item) => {
		if (data.mode !== "single") return "top";
		const first = item.data.find(point => Number.isFinite(point.value));
		return first?.value < 0 ? "bottom" : "top";
	};

	const formatAxis = (value, data) => {
		const number = Number(value);
		if (!Number.isFinite(number)) return String(value);
		const unit = data?.unit;
		const domain = data?.yDomain || [];
		if (unit === "%") {
			return formatAxisNumber(number, {
				min: domain[0],
				max: domain[1],
				splitNumber: AXIS_SPLIT_NUMBER,
				type: "percentage"
			});
		}
		return formatAxisNumber(number, {
			min: domain[0],
			max: domain[1],
			splitNumber: AXIS_SPLIT_NUMBER,
			type: ""
		});
	};

	const axisMeasureLabel = data => {
		const unit = String(data?.unit || "").trim();
		const basis = String(data?.basis || "").trim();
		if (!unit) return "";
		if (unit === "%" && basis) return `${basis} share (%)`;
		if (unit === "%") return "";
		return unit;
	};

	onMounted(() => {
		nextTick(renderChart);
		window.addEventListener("resize", resize);
	});

	watch(
		() => [props.row, props.titles],
		() => nextTick(renderChart),
		{ deep: true }
	);

	onUnmounted(() => {
		window.removeEventListener("resize", resize);
		chart?.dispose();
		chart = null;
	});
</script>

<style scoped>
	.merged-comparison {
		display: block;
		height: 100%;
		min-height: 420px;
		color: #1f2937;
	}

	.merged-chart {
		width: 100%;
		height: 100%;
		min-height: 420px;
		background: #ffffff;
	}

	.merged-empty {
		display: grid;
		min-height: 420px;
		place-items: center;
		color: #64748b;
		font-size: 13px;
		background: #ffffff;
		border: 1px solid #dbe3ee;
		border-radius: 8px;
	}
</style>
