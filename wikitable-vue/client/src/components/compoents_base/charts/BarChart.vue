<template>
	<div ref="chartEl" class="bar-chart"></div>
</template>

<script setup>
	import { ref, onMounted, watch } from "vue";
	import * as echarts from "echarts";
	const { formatAxisNumber } = require("@/js/chartValueDisplay");

	const props = defineProps({
		data: {
			type: Array,
			default: () => []
		},
		yRange: {
			type: Array,
			default: () => [0, 100]
		},
		compareData: {
			type: Array,
			default: () => []
		}
	});

	const chartEl = ref(null);
	let chartInstance = null;
	const AXIS_SPLIT_NUMBER = 4;

	const initChart = () => {
		if (!chartEl.value) return;

		chartInstance = echarts.init(chartEl.value);

		// 计算数据的最大值
		const allData = [...props.data, ...props.compareData];
		const maxValue = Math.max(...allData.map(item => item.value), 100); // 确保最小值为100

		const series = [
			{
				name: "当前数据",
				type: "bar",
				barWidth: "40%",
				data: props.data.map(item => item.value),
				itemStyle: {
					color: "#3498db"
				}
			}
		];

		// 如果有对比数据
		if (props.compareData && props.compareData.length > 0) {
			series.push({
				name: "对比数据",
				type: "bar",
				barWidth: "40%",
				data: props.compareData.map(item => item.value),
				itemStyle: {
					color: "#e74c3c"
				}
			});
		}

		const option = {
			tooltip: {
				trigger: "axis",
				axisPointer: {
					type: "shadow"
				}
			},
			grid: {
				left: "3%",
				right: "4%",
				bottom: "3%",
				containLabel: true
			},
			xAxis: {
				type: "category",
				data: props.data.map(item => item.name)
			},
			yAxis: {
				type: "value",
				min: 0,
				max: maxValue, // 使用计算的最大值
				splitNumber: AXIS_SPLIT_NUMBER,
				axisLabel: {
					formatter: value => formatAxisNumber(value, {
						min: 0,
						max: maxValue,
						splitNumber: AXIS_SPLIT_NUMBER
					})
				}
			},
			series
		};

		chartInstance.setOption(option);
	};

	onMounted(() => {
		initChart();
		window.addEventListener("resize", () => chartInstance?.resize());
	});

	watch(
		() => [props.data, props.compareData, props.yRange],
		() => {
			if (chartInstance) {
				initChart();
			}
		},
		{ deep: true }
	);
</script>

<style scoped>
	.bar-chart {
		width: 100%;
		height: 100%;
		min-height: 150px;
	}
</style>
