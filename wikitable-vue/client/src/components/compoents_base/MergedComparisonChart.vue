<template>
	<div class="merged-comparison">
		<div class="merged-summary">
			<div
				v-for="side in merged.series"
				:key="side.side"
				class="summary-item"
				:class="side.side">
				<span class="summary-label">{{ side.name }}</span>
				<strong>{{ firstDisplay(side) }}</strong>
			</div>
			<div class="summary-item delta">
				<span class="summary-label">Difference</span>
				<strong>{{ merged.stats.deltaDisplay }}</strong>
			</div>
		</div>

		<div ref="chartEl" class="merged-chart"></div>

		<div class="raw-values">
			<div
				v-for="detail in merged.rawDetails"
				:key="detail.label"
				class="raw-row">
				<span>{{ detail.label }}</span>
				<p>{{ detail.value }}</p>
			</div>
		</div>
	</div>
</template>

<script setup>
	import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
	import * as echarts from "echarts";
	const { buildMergedComparison } = require("@/js/mergedComparisonData");
	const { formatChartNumber } = require("@/js/chartValueDisplay");

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

	const merged = computed(() => buildMergedComparison(props.row, props.titles));

	const firstDisplay = series => {
		const point = series.data.find(item => item.display && item.display !== "-");
		return point?.display || "-";
	};

	const resize = () => chart?.resize();

	const renderChart = () => {
		if (!chartEl.value) return;
		if (!chart) chart = echarts.init(chartEl.value);
		chart.setOption(chartOption(merged.value), true);
	};

	const chartOption = data => {
		const isLine = data.mode === "line";
		const isSingle = data.mode === "single";
		const colors = ["#3867a8", "#c94f45"];
		const series = data.series.map((item, index) => ({
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
				show: true,
				position: pointLabelPosition(data, item),
				distance: 8,
				color: "#243447",
				fontSize: 11,
				formatter: params => params.data?.display || "-"
			},
			lineStyle: {
				width: 2.5
			},
			itemStyle: {
				color: colors[index % colors.length],
				borderRadius: isLine ? 0 : [4, 4, 0, 0]
			}
		}));

		return {
			color: colors,
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
				bottom: data.categories.length > 4 ? 70 : 42,
				containLabel: true
			},
			xAxis: {
				type: "category",
				data: data.categories,
				axisTick: { alignWithLabel: true },
				axisLabel: {
					interval: 0,
					rotate: data.categories.length > 4 ? 24 : 0,
					color: "#475569",
					fontSize: 11
				},
				axisLine: { lineStyle: { color: "#cbd5e1" } }
			},
			yAxis: {
				type: "value",
				min: data.yDomain[0],
				max: data.yDomain[1],
				axisLabel: {
					color: "#475569",
					formatter: value => formatAxis(value, data.unit)
				},
				splitLine: { lineStyle: { color: "#e5eaf1" } },
				axisLine: { show: false }
			},
			series,
			dataZoom:
				data.categories.length > 8
					? [
							{
								type: "slider",
								height: 18,
								bottom: 12,
								start: 0,
								end: Math.min(100, (8 / data.categories.length) * 100)
							}
					  ]
					: []
		};
	};

	const pointLabelPosition = (data, item) => {
		if (data.mode !== "single") return "top";
		const first = item.data.find(point => Number.isFinite(point.value));
		return first?.value < 0 ? "bottom" : "top";
	};

	const formatAxis = (value, unit) => {
		const number = Number(value);
		if (!Number.isFinite(number)) return String(value);
		if (unit === "%" || unit === "% of GDP") {
			return formatChartNumber(number, "percentage");
		}
		return formatChartNumber(number, "");
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
		display: grid;
		grid-template-rows: auto minmax(300px, 1fr) auto;
		gap: 14px;
		height: 100%;
		min-height: 520px;
		color: #1f2937;
	}

	.merged-summary {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 10px;
	}

	.summary-item {
		min-width: 0;
		border: 1px solid #dbe3ee;
		border-left: 4px solid #94a3b8;
		border-radius: 8px;
		background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
		padding: 10px 12px;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
	}

	.summary-item.left {
		border-left-color: #3867a8;
	}

	.summary-item.right {
		border-left-color: #c94f45;
	}

	.summary-item.delta {
		border-left-color: #64748b;
	}

	.summary-label {
		display: block;
		margin-bottom: 5px;
		color: #64748b;
		font-size: 11px;
		font-weight: 650;
	}

	.summary-item strong {
		display: block;
		overflow-wrap: anywhere;
		font-size: 15px;
		line-height: 1.25;
	}

	.merged-chart {
		width: 100%;
		height: 100%;
		min-height: 300px;
		border: 1px solid #dbe3ee;
		border-radius: 8px;
		background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
	}

	.raw-values {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 10px;
	}

	.raw-row {
		border: 1px solid #dbe3ee;
		border-radius: 8px;
		background: #fbfdff;
		padding: 9px 11px;
	}

	.raw-row span {
		display: block;
		margin-bottom: 4px;
		color: #64748b;
		font-size: 12px;
		font-weight: 600;
	}

	.raw-row p {
		margin: 0;
		color: #1f2937;
		font-size: 12px;
		line-height: 1.4;
		overflow-wrap: anywhere;
	}

	@media (max-width: 760px) {
		.merged-summary,
		.raw-values {
			grid-template-columns: 1fr;
		}
	}
</style>
