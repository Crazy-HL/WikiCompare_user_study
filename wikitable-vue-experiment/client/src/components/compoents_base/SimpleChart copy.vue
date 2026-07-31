<template>
	<div class="simple-chart">
		<!-- 文本显示 -->
		<template v-if="visualization === 'text-only'">
			<div
				class="simple-text"
				@click="handleTextClick"
				@mouseenter="handleTextHover"
				@mouseleave="resetHover">
				{{ formatSimpleText(processedField) }}
			</div>
			<div v-if="isTextHovered" class="text-tooltip">点击查看详情</div>
		</template>

		<!-- 饼图 (D3实现) -->
		<template v-else-if="visualization === 'pie-chart'">
			<div
				v-if="hasData && isValidPieData"
				class="d3-chart-container"
				ref="pieContainer"></div>
			<div v-else class="no-data">-</div>
		</template>

		<!-- 柱状图 (D3实现) -->
		<template v-else-if="visualization === 'bar-chart'">
			<div v-if="hasData" class="d3-chart-container" ref="barContainer"></div>
			<div v-else class="no-data">-</div>
		</template>

		<!-- 折线图 (D3实现) -->
		<template v-else-if="visualization === 'line-chart'">
			<div v-if="hasData" class="d3-chart-container" ref="lineContainer"></div>
			<div v-else class="no-data">-</div>
		</template>

		<!-- 默认显示 -->
		<template v-else>
			<div
				class="simple-text"
				@click="handleTextClick"
				@mouseenter="handleTextHover"
				@mouseleave="resetHover">
				{{ formatSimpleText(processedField) }}
			</div>
			<div v-if="isTextHovered" class="text-tooltip">点击查看详情</div>
		</template>
	</div>
</template>

<script>
	import { computed, ref, onMounted, watch, nextTick } from "vue";
	import * as d3 from "d3";

	export default {
		props: {
			field: {
				type: [Object, Array, String, Number],
				default: null
			},
			type: {
				type: String,
				default: ""
			},
			visualization: {
				type: String,
				default: ""
			},
			fieldKey: {
				type: String,
				default: ""
			},
			unifiedMax: {
				type: Number,
				default: null
			}
		},

		emits: ["chartClick"],

		setup(props, { emit }) {
			const hoveredIndex = ref(null);
			const activeIndex = ref(null);
			const isTextHovered = ref(false);

			// 容器引用
			const pieContainer = ref(null);
			const barContainer = ref(null);
			const lineContainer = ref(null);

			// 颜色定义
			const colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"];
			const remainderColor = "#f0f0f0";

			// 处理后的字段数据
			const processedField = computed(() => {
				if (!props.field) return null;

				// 如果是数组，处理每个元素
				if (Array.isArray(props.field)) {
					return props.field.map(item => {
						if (typeof item === "object" && item !== null) {
							return {
								value: item.value ?? item.raw,
								raw: item.raw,
								...(item.unit && { unit: item.unit }),
								...(item.currency && { currency: item.currency }),
								...(item.year && { year: item.year })
							};
						}
						return { value: item, raw: item };
					});
				}

				// 如果是对象
				if (typeof props.field === "object" && props.field !== null) {
					return {
						value: props.field.value ?? props.field.raw,
						raw: props.field.raw,
						...(props.field.unit && { unit: props.field.unit }),
						...(props.field.currency && { currency: props.field.currency }),
						...(props.field.year && { year: props.field.year })
					};
				}

				// 原始值
				return { value: props.field, raw: props.field };
			});

			// 初始化图表
			onMounted(() => {
				watch(
					() => [processedField.value, props.visualization, props.unifiedMax],
					() => {
						nextTick(() => {
							if (
								props.visualization === "pie-chart" &&
								hasData.value &&
								isValidPieData.value
							) {
								renderPieChart();
							} else if (props.visualization === "bar-chart" && hasData.value) {
								renderBarChart();
							} else if (
								props.visualization === "line-chart" &&
								hasData.value
							) {
								renderLineChart();
							}
						});
					},
					{ immediate: true, deep: true }
				);
			});

			// 渲染饼图（添加剩余比例）
			const renderPieChart = () => {
				if (!pieContainer.value) return;

				// 清除旧图表
				d3.select(pieContainer.value).selectAll("*").remove();

				const container = d3.select(pieContainer.value);
				const containerWidth = pieContainer.value.clientWidth;
				const containerHeight = pieContainer.value.clientHeight;

				// 使用高度作为基准尺寸，确保饼图大小不变
				const size = containerHeight * 0.9; // 饼图大小基于高度
				const radius = size / 2;

				// 创建SVG，宽度100%，高度固定
				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${containerWidth} ${containerHeight}`)
					.append("g")
					.attr(
						"transform",
						`translate(${containerWidth / 2}, ${containerHeight / 2})`
					);

				// 判断是否是单值饼图
				const isSingleValue = props.fieldKey === "Inflation (CPI)";

				// 处理数据 - 如果是单值，添加剩余部分
				const processedData = isSingleValue
					? [
							{
								...pieData.value[0],
								color: colors[0],
								isMainValue: true
							},
							{
								value: Math.max(0, 100 - pieData.value[0].value),
								name: "剩余",
								color: remainderColor,
								isRemainder: true,
								index: 1
							}
					  ]
					: pieData.value.map((d, i) => ({
							...d,
							color: colors[i % colors.length],
							isMainValue: true
					  }));

				const pie = d3
					.pie()
					.value(d => d.value)
					.sort(null);

				const arc = d3
					.arc()
					.innerRadius(0)
					.outerRadius(radius * 0.9)
					.cornerRadius(2);

				const arcs = svg
					.selectAll(".arc")
					.data(pie(processedData))
					.enter()
					.append("g")
					.attr("class", "arc");

				// 创建tooltip
				const tooltip = container
					.append("div")
					.attr("class", "d3-tooltip")
					.style("position", "absolute")
					.style("visibility", "hidden")
					.style("background", "rgba(0,0,0,0.8)")
					.style("color", "white")
					.style("padding", "6px 12px")
					.style("border-radius", "4px")
					.style("font-size", "12px");

				// 绘制扇形
				arcs
					.append("path")
					.attr("d", arc)
					.attr("fill", d => d.data.color)
					.style("opacity", d => (d.data.isRemainder ? 0.6 : 0.8))
					.style("stroke", "#fff")
					.style("stroke-width", 1)
					.on("mouseover", function (event, d) {
						if (d.data.isRemainder) return;

						hoveredIndex.value = d.data.index;
						d3.select(this)
							.transition()
							.duration(200)
							.style("opacity", 1)
							.attr("transform", "scale(1.05)");

						tooltip
							.style("visibility", "visible")
							.html(
								`${d.data.name}: ${d.data.value.toFixed(1)}${
									props.type === "percentage" ? "%" : ""
								}`
							);
					})
					.on("mousemove", function (event) {
						tooltip
							.style("top", event.offsetY + 10 + "px")
							.style("left", event.offsetX + 10 + "px");
					})
					.on("mouseout", function (event, d) {
						if (d.data.isRemainder) return;

						hoveredIndex.value = null;
						d3.select(this)
							.transition()
							.duration(200)
							.style("opacity", d.data.isRemainder ? 0.6 : 0.8)
							.attr("transform", "scale(1)");

						tooltip.style("visibility", "hidden");
					})
					.on("click", function (event, d) {
						if (d.data.isRemainder) return;

						activeIndex.value = d.data.index;
						emit("chartClick", {
							type: "pie",
							index: d.data.index,
							data: d.data,
							value: d.data.value
						});
					});

				// 单值饼图的中心文字
				if (isSingleValue) {
					svg
						.append("text")
						.attr("text-anchor", "middle")
						.attr("dy", ".3em")
						.text(
							`${pieData.value[0].value.toFixed(1)}${
								props.type === "percentage" ? "%" : ""
							}`
						)
						.style("font-size", "14px")
						.style("fill", "#333");
				}

				// 多值饼图的图例 - 修改为右上角放置
				if (!isSingleValue && pieData.value.length > 1) {
					const legend = svg.append("g").attr("class", "legend");
					const legendItemSize = 12;
					const legendSpacing = 4;
					const legendStartX = containerWidth / 2 - 100; // 从中心向右偏移
					const legendStartY = -containerHeight / 2 + 20; // 从顶部向下偏移

					pieData.value.forEach((d, i) => {
						const legendItem = legend
							.append("g")
							.attr(
								"transform",
								`translate(${legendStartX}, ${
									legendStartY + i * (legendItemSize + legendSpacing)
								})`
							);

						legendItem
							.append("rect")
							.attr("width", legendItemSize)
							.attr("height", legendItemSize)
							.attr("fill", colors[i % colors.length]);

						legendItem
							.append("text")
							.attr("x", legendItemSize + 4)
							.attr("y", legendItemSize - 2)
							.text(`${d.name}: ${d.value.toFixed(1)}%`)
							.style("font-size", "10px")
							.style("fill", "#333");
					});
				}
			};

			const renderBarChart = () => {
				if (!barContainer.value) return;

				d3.select(barContainer.value).selectAll("*").remove();

				const container = d3.select(barContainer.value);
				const width = barContainer.value.clientWidth;
				const height = barContainer.value.clientHeight;
				const margin = { top: 10, right: 10, bottom: 30, left: 10 }; // 减少左侧边距，因为我们不需要Y轴了

				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${width} ${height}`);

				// 使用统一的最大值或计算最大值
				const maxYValue =
					props.unifiedMax !== null
						? props.unifiedMax
						: d3.max(simpleBarData.value, d => d.value) * 1.1 || 1; // 增加10%缓冲

				// 确保最小值至少为0
				const minYValue = Math.min(
					0,
					d3.min(simpleBarData.value, d => d.value) || 0
				);

				// 创建Y轴比例尺（但不绘制Y轴）
				const y = d3
					.scaleLinear()
					.domain([minYValue, maxYValue])
					.range([height - margin.bottom, margin.top]);

				// 设定柱子最大宽度和最小间距
				const maxBarWidth = 60;
				const minSpacing = 10;
				const availableWidth = width - margin.left - margin.right;
				const barCount = simpleBarData.value.length;
				const barWidth = Math.min(
					maxBarWidth,
					Math.max(20, availableWidth / barCount - minSpacing)
				);

				// 计算起始位置使柱子居中
				const totalBarsWidth =
					barWidth * barCount + minSpacing * (barCount - 1);
				const startX = margin.left + (availableWidth - totalBarsWidth) / 2;

				// 绘制柱子
				svg
					.selectAll(".bar")
					.data(simpleBarData.value)
					.enter()
					.append("rect")
					.attr("class", "bar")
					.attr("x", (d, i) => startX + i * (barWidth + minSpacing))
					.attr("y", d => y(Math.max(0, d.value))) // 确保柱子不会超出底部
					.attr("width", barWidth)
					.attr("height", d => Math.abs(y(d.value) - y(0))) // 计算绝对高度
					.attr("fill", (d, i) => colors[i % colors.length])
					.style("opacity", 0.8);

				// 在每个柱子下方添加数值标签
				svg
					.selectAll(".bar-label")
					.data(simpleBarData.value)
					.enter()
					.append("text")
					.attr("class", "bar-label")
					.attr(
						"x",
						(d, i) => startX + i * (barWidth + minSpacing) + barWidth / 2
					)
					.attr("y", height - 5)
					.attr("text-anchor", "middle")
					.attr("font-size", "10px")
					.attr("fill", "#666")
					.text(d => formatNumber(d.value, props.fieldKey));
			};

			// 修改后的 renderLineChart 函数
			const renderLineChart = () => {
				if (!lineContainer.value) return;

				d3.select(lineContainer.value).selectAll("*").remove();

				const container = d3.select(lineContainer.value);
				const width = lineContainer.value.clientWidth;
				const height = lineContainer.value.clientHeight;
				const margin = { top: 10, right: 10, bottom: 30, left: 10 };

				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${width} ${height}`);

				const x = d3
					.scaleLinear()
					.domain([0, lineData.value.length - 1])
					.range([margin.left, width - margin.right]);

				const y = d3
					.scaleLinear()
					.domain([
						d3.min(lineData.value, d => d.y),
						d3.max(lineData.value, d => d.y)
					])
					.range([height - margin.bottom, margin.top]);

				// 绘制折线
				const line = d3
					.line()
					.x((d, i) => x(i))
					.y(d => y(d.y))
					.curve(d3.curveMonotoneX);

				svg
					.append("path")
					.datum(lineData.value)
					.attr("fill", "none")
					.attr("stroke", "#3498db")
					.attr("stroke-width", 2)
					.attr("d", line);

				// 绘制数据点
				svg
					.selectAll(".dot")
					.data(lineData.value)
					.enter()
					.append("circle")
					.attr("class", "dot")
					.attr("cx", (d, i) => x(i))
					.attr("cy", d => y(d.y))
					.attr("r", 3)
					.attr("fill", "#3498db");

				// 在每个数据点下方添加数值标签
				svg
					.selectAll(".line-label")
					.data(lineData.value)
					.enter()
					.append("text")
					.attr("class", "line-label")
					.attr("x", (d, i) => x(i))
					.attr("y", height - 5)
					.attr("text-anchor", "middle")
					.attr("font-size", "10px")
					.attr("fill", "#666")
					.text(d => formatNumber(d.y, props.fieldKey));
			};

			// 交互处理函数
			const handleTextHover = () => {
				isTextHovered.value = true;
			};

			const resetHover = () => {
				hoveredIndex.value = null;
				isTextHovered.value = false;
			};

			const handleTextClick = () => {
				emit("chartClick", {
					type: "text",
					data: processedField.value,
					value: processedField.value
				});
			};

			const formatNumber = (value, fieldKey) => {
				const num = Number(value);
				if (isNaN(num)) return "0";

				// 百分比特殊处理
				if (props.type === "percentage") {
					return num.toFixed(1) + "%";
				}

				// 统一中文单位显示规则
				if (num >= 100000000) {
					// 1亿以上
					return (num / 100000000).toFixed(2) + "亿";
				} else if (num >= 10000) {
					// 1万以上
					return (num / 10000).toFixed(1) + "万";
				} else if (num >= 1000) {
					// 1千以上
					return (num / 1000).toFixed(1) + "千";
				} else {
					// 小于1千
					return num.toFixed(0);
				}
			};

			// 数据处理函数
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

			const isValidPieData = computed(() => {
				if (!pieData.value.length) return false;
				return pieData.value.every(
					item => !isYearEntry(item.name) && !isYearEntry(item.value)
				);
			});

			const pieData = computed(() => {
				if (!processedField.value) return [];

				const processItem = (item, index) => {
					// 获取原始值，处理各种可能的数据结构
					let rawValue;
					if (typeof item === "object" && item !== null) {
						rawValue = item.raw || item.value || item;
					} else {
						rawValue = item;
					}

					// 如果是年份条目则跳过
					if (isYearEntry(rawValue)) return null;

					// 转换为数值
					const value = safeToNumber(rawValue, props.fieldKey);
					if (value === null) return null;

					// 获取名称，处理各种可能的数据结构
					let name = "项目";
					if (typeof item === "object" && item !== null) {
						// 确保 raw 是字符串才调用 replace
						const rawText =
							typeof item.raw === "string"
								? item.raw
								: typeof item.value === "string"
								? item.value
								: JSON.stringify(item);
						name = rawText.replace(/:\s*\d+\.?\d*%?/g, "").trim();
					} else if (typeof item === "string") {
						name = item.replace(/:\s*\d+\.?\d*%?/g, "").trim();
					}

					// 如果是年份条目则跳过
					if (isYearEntry(name)) return null;

					return {
						value: Math.min(100, Math.max(0, value)),
						name: name || "项目",
						index: index
					};
				};

				if (Array.isArray(processedField.value)) {
					return processedField.value
						.map((item, index) => processItem(item, index))
						.filter(item => item !== null && !isYearEntry(item.name));
				}

				const result = processItem(processedField.value, 0);
				return result ? [result] : [];
			});

			const safeToNumber = (value, fieldKey) => {
				if (value === null || value === undefined) return 0;
				if (typeof value === "number") return value;

				if (typeof value === "string") {
					// 处理中文单位
					const yiMatch = value.match(/(-?[\d.]+)亿/);
					if (yiMatch) return parseFloat(yiMatch[1]) * 100000000;

					const wanMatch = value.match(/(-?[\d.]+)万/);
					if (wanMatch) return parseFloat(wanMatch[1]) * 10000;

					const qianMatch = value.match(/(-?[\d.]+)千/);
					if (qianMatch) return parseFloat(qianMatch[1]) * 1000;

					// 处理百分比
					const percentMatch = value.match(/(-?\d+\.?\d*)%/);
					if (percentMatch) return parseFloat(percentMatch[1]);

					// 默认数字
					const num = parseFloat(value.replace(/[^\d.-]/g, ""));
					return isNaN(num) ? 0 : num;
				}

				if (typeof value === "object") {
					return safeToNumber(value.value || value.raw, fieldKey);
				}

				return 0;
			};

			const formatSimpleText = value => {
				if (!value) return "-";

				// 处理数组
				if (Array.isArray(value)) {
					const items = value.map(item => {
						if (typeof item === "object" && item !== null) {
							let text = item.raw || item.value || JSON.stringify(item);
							if (item.unit) text += ` ${item.unit}`;
							if (item.year) text += ` (${item.year})`;
							return text;
						}
						return item;
					});
					return items.length > 2
						? items.slice(0, 2).join("; ") + "..."
						: items.join("; ");
				}

				// 处理对象
				if (typeof value === "object" && value !== null) {
					let text = value.raw || value.value || "-";
					if (value.unit) text += ` ${value.unit}`;
					if (value.year) text += ` (${value.year})`;
					return text;
				}

				// 处理原始值
				return value.toString().length > 50
					? value.toString().substring(0, 50) + "..."
					: value.toString();
			};

			const simpleBarData = computed(() => {
				if (!processedField.value) return [];

				let values = [];

				if (Array.isArray(processedField.value)) {
					values = processedField.value
						.filter(item => {
							const value = item?.value || item?.raw;
							return (
								value !== undefined && value !== null && !isYearEntry(value)
							);
						})
						.map(item => safeToNumber(item.value || item.raw, props.fieldKey));
				} else {
					values = [
						safeToNumber(
							processedField.value.value || processedField.value.raw,
							props.fieldKey
						)
					].filter(v => v !== null);
				}

				if (values.length === 0) return [];

				return values.map((v, index) => ({
					value: v,
					height: v,
					color: colors[index % colors.length],
					index: index
				}));
			});

			const lineData = computed(() => {
				if (!processedField.value) return [];

				if (Array.isArray(processedField.value)) {
					return processedField.value
						.filter(item => {
							const value = item?.value || item?.raw;
							return (
								value !== undefined && value !== null && !isYearEntry(value)
							);
						})
						.map((item, index) => {
							const value = safeToNumber(
								item.value || item.raw,
								props.fieldKey
							);
							return {
								x: index,
								y: value,
								raw: item.raw || item.value,
								index: index
							};
						});
				}

				const value = safeToNumber(
					processedField.value.value || processedField.value.raw,
					props.fieldKey
				);
				return value !== null
					? [
							{
								x: 0,
								y: value,
								raw: processedField.value.raw || processedField.value.value,
								index: 0
							}
					  ]
					: [];
			});

			const hasData = computed(() => {
				if (!processedField.value) return false;
				if (Array.isArray(processedField.value))
					return processedField.value.length > 0;
				if (typeof processedField.value === "object")
					return Object.keys(processedField.value).length > 0;
				return String(processedField.value).trim().length > 0;
			});

			return {
				hoveredIndex,
				activeIndex,
				isTextHovered,
				pieContainer,
				barContainer,
				lineContainer,
				handleTextHover,
				resetHover,
				handleTextClick,
				formatSimpleText,
				hasData,
				isValidPieData,
				pieData,
				simpleBarData,
				lineData,
				formatNumber,
				processedField
			};
		}
	};
</script>

<style scoped>
	.simple-chart {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		font-family: Arial, sans-serif;
	}

	/* 文本样式 */
	.simple-text {
		text-align: center;
		font-size: 14px;
		word-break: break-word;
		padding: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
		border-radius: 4px;
		background-color: #f8f9fa;
		max-width: 100%;
	}

	.simple-text:hover {
		background-color: #e9ecef;
		transform: translateY(-2px);
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
	}

	.text-tooltip {
		position: absolute;
		top: -25px;
		left: 50%;
		transform: translateX(-50%);
		background-color: rgba(0, 0, 0, 0.8);
		color: white;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 12px;
		pointer-events: none;
		white-space: nowrap;
		z-index: 10;
	}

	/* D3图表容器 */
	.d3-chart-container {
		width: 100%;
		height: 120px; /* 固定高度 */
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	/* D3 tooltip样式 */
	.d3-tooltip {
		z-index: 10;
		white-space: nowrap;
		pointer-events: none;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
	}

	/* 无数据样式 */
	.no-data {
		color: #999;
		font-style: italic;
		padding: 10px;
	}

	/* Y轴样式 */
	.y-axis line {
		stroke: #e0e0e0;
		stroke-dasharray: 2, 2;
	}

	.y-axis text {
		font-size: 10px;
		fill: #666;
	}

	/* 响应式调整 */
	@media (max-width: 768px) {
		.simple-text {
			font-size: 12px;
		}

		.d3-chart-container {
			min-height: 60px;
		}
	}

	/* 添加在style部分的末尾 */
	.bar-label,
	.line-label {
		font-family: Arial, sans-serif;
		pointer-events: none;
		user-select: none;
	}

	@media (max-width: 768px) {
		.bar-label,
		.line-label {
			font-size: 8px;
		}
	}
</style>
