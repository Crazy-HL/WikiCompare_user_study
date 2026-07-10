<template>
	<div ref="chartRef" class="combined-chart"></div>
</template>

<script setup>
	import { ref, onMounted, watch, onUnmounted } from "vue";
	import * as echarts from "echarts";
	const { formatAxisNumber } = require("@/js/chartValueDisplay");

	const props = defineProps({
		data: {
			type: Array,
			required: true
		},
		fieldKey: {
			type: String,
			required: true
		},
		sources: {
			type: Object,
			required: true
		}
	});

	const chartRef = ref(null);
	let chartInstance = null;
	const AXIS_SPLIT_NUMBER = 4;

	const initChart = () => {
		if (!chartRef.value) return;

		// 按来源分组数据
		const groupedData = {};
		props.data.forEach(item => {
			if (!groupedData[item.source]) {
				groupedData[item.source] = [];
			}
			groupedData[item.source].push(item);
		});

		// 准备系列数据
		const series = [];
		const colors = ["#4285F4", "#EA4335"]; // 蓝色和红色

		Object.entries(groupedData).forEach(([source, data], index) => {
			// 按年份排序
			data.sort((a, b) => (a.year || 0) - (b.year || 0));

			series.push({
				name: source,
				type: "line",
				smooth: true, // 圆滑折线设置
				data: data.map(item => ({
					value: item.value,
					raw: item.raw,
					year: item.year
				})),
				symbol: "circle",
				symbolSize: 8,
				itemStyle: {
					color: colors[index % colors.length]
				},
				lineStyle: {
					width: 3
				},
				label: {
					show: true,
					formatter: ({ data }) => data.raw
				}
			});
		});

		// 提取所有年份并去重排序
		const allYears = [
			...new Set(props.data.map(item => item.year).filter(Boolean))
		].sort();
		const values = props.data.map(item => Number(item.value)).filter(Number.isFinite);
		const minValue = values.length ? Math.min(...values) : 0;
		const maxValue = values.length ? Math.max(...values) : 100;

		const option = {
			title: {
				text: `${props.fieldKey} 对比`,
				left: "center"
			},
			tooltip: {
				trigger: "axis",
				formatter: params => {
					return params
						.map(param => {
							const { seriesName, data } = param;
							return `${seriesName}: ${data.raw}`;
						})
						.join("<br/>");
				}
			},
			legend: {
				data: Object.keys(groupedData),
				top: 30
			},
			grid: {
				top: 80,
				containLabel: true
			},
			xAxis: {
				type: "category",
				data: allYears,
				axisLabel: {
					formatter: value => `${value}年`
				}
			},
			yAxis: {
				type: "value",
				min: minValue,
				max: maxValue,
				splitNumber: AXIS_SPLIT_NUMBER,
				axisLabel: {
					formatter: value => formatAxisNumber(value, {
						min: minValue,
						max: maxValue,
						splitNumber: AXIS_SPLIT_NUMBER,
						type: "percentage"
					})
				}
			},
			series
		};

		if (!chartInstance) {
			chartInstance = echarts.init(chartRef.value);
		}
		chartInstance.setOption(option);
	};

	onMounted(() => {
		initChart();
		window.addEventListener("resize", handleResize);
	});

	const handleResize = () => {
		if (chartInstance) {
			chartInstance.resize();
		}
	};

	watch(
		() => props.data,
		() => {
			initChart();
		},
		{ deep: true }
	);

	onUnmounted(() => {
		window.removeEventListener("resize", handleResize);
		if (chartInstance) {
			chartInstance.dispose();
		}
	});
</script>

<style scoped>
	.combined-chart {
		width: 100%;
		height: 100%;
	}
</style>
