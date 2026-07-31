<template>
	<div ref="chartContainer" class="pie-chart-container">
		<div v-if="!hasValidData" class="no-data">-</div>
	</div>
</template>

<script setup>
	import { ref, computed, onMounted, watch } from "vue";
	import * as d3 from "d3";

	const props = defineProps({
		data: {
			type: Array,
			default: () => [],
			validator: value => value.every(item => "name" in item && "value" in item)
		},
		showLegend: {
			type: Boolean,
			default: false
		},
		isSingleValue: {
			type: Boolean,
			default: false
		}
	});

	const emit = defineEmits(["itemClick", "dataOutput"]);

	const chartContainer = ref(null);
	const colors = [
		"#3498db",
		"#e74c3c",
		"#2ecc71",
		"#f39c12",
		"#9b59b6",
		"#1abc9c"
	];
	const remainderColor = "#f0f0f0";

	const isYearEntry = value => {
		if (typeof value !== "string") return false;
		const trimmedValue = value.trim();
		return (
			/^(\()?\d{4}(\))?\s*:?/.test(trimmedValue) ||
			/^\(?FY\s*\d{4}\)?\s*:?/i.test(trimmedValue) ||
			/^(\()?\d{4}\s*[-–]\s*\d{2,4}(\))?\s*:?/.test(trimmedValue) ||
			/^(Year|Yr|Annual)\s*\d{4}/i.test(trimmedValue)
		);
	};

	const filteredData = computed(() => {
		return props.data.filter(item => {
			const name = String(item.name || "");
			const value = String(item.value || "");
			return !isYearEntry(name) && !isYearEntry(value);
		});
	});

	const hasValidData = computed(() => filteredData.value.length > 0);

	const processedData = computed(() => {
		if (!hasValidData.value) return [];

		// 如果是单值饼图，添加剩余部分
		if (props.isSingleValue) {
			const mainValue = Math.min(
				100,
				Math.max(0, Number(filteredData.value[0].value) || 0)
			);
			return [
				{ ...filteredData.value[0], value: mainValue, isMain: true, index: 0 },
				{
					name: "剩余",
					value: Math.max(0, 100 - mainValue),
					isRemainder: true,
					index: 1
				}
			];
		}

		// 多值饼图直接返回处理后的数据
		return filteredData.value.map((item, index) => ({
			...item,
			value: Math.min(100, Math.max(0, Number(item.value) || 0)),
			index
		}));
	});

	let svg, arc, pie, tooltip;

	const initChart = () => {
		if (!chartContainer.value || !hasValidData.value) return;

		d3.select(chartContainer.value).selectAll("*").remove();

		const container = d3.select(chartContainer.value);
		const width = chartContainer.value.clientWidth;
		const height = chartContainer.value.clientHeight;
		const radius = (Math.min(width, height) / 2) * 0.7;

		svg = container
			.append("svg")
			.attr("width", "100%")
			.attr("height", "100%")
			.attr("viewBox", `0 0 ${width} ${height}`);

		const pieGroup = svg
			.append("g")
			.attr("transform", `translate(${width / 2}, ${height / 2.5})`);

		pie = d3
			.pie()
			.value(d => d.value)
			.sort(null);

		arc = d3.arc().innerRadius(0).outerRadius(radius).cornerRadius(4);

		tooltip = container
			.append("div")
			.attr("class", "chart-tooltip")
			.style("opacity", 0);

		const arcs = pieGroup
			.selectAll(".arc")
			.data(pie(processedData.value))
			.enter()
			.append("g")
			.attr("class", "arc");

		arcs
			.append("path")
			.attr("d", arc)
			.attr("fill", d =>
				d.data.isRemainder
					? remainderColor
					: colors[d.data.index % colors.length]
			)
			.style("opacity", d => (d.data.isRemainder ? 0.6 : 0.8))
			.style("stroke", "#fff")
			.style("stroke-width", 1.5)
			.style("transition", "opacity 0.2s")
			.on("mouseover", function (event, d) {
				if (d.data.isRemainder) return;

				d3.select(this).transition().duration(200).style("opacity", 1);
				tooltip.transition().duration(200).style("opacity", 1);
				tooltip
					.html(
						`
          <div class="tooltip-title">${d.data.name}</div>
          <div class="tooltip-value">${d.data.value.toFixed(1)}%</div>
        `
					)
					.style("left", event.pageX + 15 + "px")
					.style("top", event.pageY - 30 + "px");
			})
			.on("mouseout", function () {
				d3.select(this).transition().duration(200).style("opacity", 0.8);
				tooltip.transition().duration(200).style("opacity", 0);
			})
			.on("click", (event, d) => {
				if (d.data.isRemainder) return;
				emit("itemClick", d.data);
			});

		// 单值饼图显示中心数值
		if (props.isSingleValue) {
			pieGroup
				.append("text")
				.attr("text-anchor", "middle")
				.attr("dy", ".3em")
				.text(`${filteredData.value[0].value.toFixed(1)}%`)
				.style("font-size", "16px")
				.style("fill", "#333")
				.style("font-weight", "500");
		}

		// 多值饼图显示图例
		if (props.showLegend && !props.isSingleValue) {
			const legendData = processedData.value.filter(d => !d.isRemainder);
			const legendGroup = svg.append("g").attr("class", "legend");

			const legendItemHeight = 20;
			const legendSpacing = 6;
			const legendPadding = 10;

			legendData.forEach((d, i) => {
				const g = legendGroup
					.append("g")
					.attr("class", "legend-item")
					.attr(
						"transform",
						`translate(${width - 150}, ${
							legendPadding + i * (legendItemHeight + legendSpacing)
						})`
					)
					.style("cursor", "pointer")
					.on("click", () => emit("itemClick", d));

				g.append("rect")
					.attr("width", 14)
					.attr("height", 14)
					.attr("rx", 2)
					.attr("ry", 2)
					.attr("fill", colors[d.index % colors.length]);

				g.append("text")
					.attr("x", 20)
					.attr("y", 11)
					.text(`${d.name} (${d.value}%)`)
					.style("font-size", "12px")
					.style("fill", "#333")
					.style("font-family", "Arial, sans-serif");
			});
		}
	};

	onMounted(() => {
		initChart();
		window.addEventListener("resize", initChart);
	});

	watch(() => [props.data, props.showLegend, props.isSingleValue], initChart, {
		deep: true
	});
</script>

<style scoped>
	.pie-chart-container {
		width: 100%;
		height: 100%;
		min-height: 260px;
		position: relative;
		background: #fff;
		border-radius: 8px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		transition: box-shadow 0.3s ease;
	}

	.pie-chart-container:hover {
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.no-data {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		color: #999;
		font-size: 14px;
		font-family: Arial, sans-serif;
	}

	.chart-tooltip {
		position: absolute;
		padding: 10px 12px;
		background: rgba(0, 0, 0, 0.85);
		color: white;
		border-radius: 6px;
		font-size: 13px;
		font-family: Arial, sans-serif;
		pointer-events: none;
		z-index: 10;
		transition: all 0.2s;
		box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
		max-width: 200px;
		line-height: 1.5;
	}

	.tooltip-title {
		font-weight: 600;
		margin-bottom: 4px;
		color: #fff;
	}

	.tooltip-value {
		font-weight: 500;
		color: #f0f0f0;
	}
</style>
