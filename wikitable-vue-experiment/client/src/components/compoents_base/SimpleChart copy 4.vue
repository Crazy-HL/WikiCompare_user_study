<template>
	<div class="simple-chart">
		<!-- 文本显示 -->
		<template v-if="visualization === 'text-only'">
			<!-- GDP Rank 的直接显示 -->
			<div v-if="fieldKey === 'GDP rank'" class="gdp-rank-direct-display">
				{{ getRawTextForRank(processedField) }}
			</div>
			<!-- 其他文本字段保持原样 -->
			<div
				v-else
				class="simple-text"
				@click="handleTextClick"
				@mouseenter="handleTextHover"
				@mouseleave="resetHover">
				{{ formatSimpleText(processedField) }}
			</div>
			<div v-if="isTextHovered && fieldKey !== 'GDP rank'" class="text-tooltip">
				点击查看详情
			</div>
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

		<!-- 堆叠图 -->
		<template v-else-if="visualization === 'stacked-chart'">
			<div
				v-if="hasData"
				class="d3-chart-container"
				ref="stackedContainer"></div>
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
			},
			categoryColors: {
				type: Object,
				default: () => ({})
			}
		},

		emits: ["chartClick"],

		setup(props, { emit }) {
			const hoveredIndex = ref(null);
			const activeIndex = ref(null);
			const isTextHovered = ref(false);

			const pieContainer = ref(null);
			const barContainer = ref(null);
			const lineContainer = ref(null);
			const stackedContainer = ref(null);

			const colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"];
			const remainderColor = "#f0f0f0";

			const isYearEntry = value => {
				if (typeof value !== "string") return false;
				const trimmedValue = value.trim();
				return (
					/^\(\d{4}.*\)$/.test(trimmedValue) ||
					/^\(\d{4}\)(\[\d+\])?$/.test(trimmedValue)
				);
			};

			const safeToNumber = value => {
				if (value === null || value === undefined) return 0;
				if (typeof value === "number") return value;
				if (typeof value === "string") {
					if (value.includes("亿"))
						return parseFloat(value.replace(/[^\d.-]/g, "")) * 100000000;
					if (value.includes("万"))
						return parseFloat(value.replace(/[^\d.-]/g, "")) * 10000;
					if (value.includes("千"))
						return parseFloat(value.replace(/[^\d.-]/g, "")) * 1000;
					const num = parseFloat(value.replace(/[^\d,.-]/g, ""));
					return isNaN(num) ? 0 : num;
				}
				if (typeof value === "object")
					return safeToNumber(value.value || value.raw);
				return 0;
			};

			const processedField = computed(() => {
				const field = props.field;
				if (!field || (Array.isArray(field) && field.length === 0)) return [];
				const fieldAsArray = Array.isArray(field) ? field : [field];
				return fieldAsArray
					.map(item => {
						if (typeof item === "object" && item !== null) {
							return {
								raw: item.raw ?? item.value ?? JSON.stringify(item),
								value: item.value ?? item.raw,
								label: item.label || item.raw,
								parent: item.parent || null
							};
						}
						return {
							raw: String(item),
							value: item,
							label: String(item),
							parent: null
						};
					})
					.filter(
						item =>
							item.raw &&
							String(item.raw).trim() !== "" &&
							!isYearEntry(String(item.raw))
					);
			});

			const getRawTextForRank = field => {
				if (!field || field.length === 0) return "-";
				return field.map(item => item.raw).join("\n");
			};

			onMounted(() => {
				watch(
					() => [processedField.value, props.visualization, props.unifiedMax],
					() => {
						nextTick(() => {
							if (
								props.visualization === "pie-chart" &&
								hasData.value &&
								isValidPieData.value
							)
								renderPieChart();
							else if (props.visualization === "bar-chart" && hasData.value)
								renderBarChart();
							else if (props.visualization === "line-chart" && hasData.value)
								renderLineChart();
							else if (props.visualization === "stacked-chart" && hasData.value)
								renderStackedChart();
						});
					},
					{ immediate: true, deep: true }
				);
			});

			const renderPieChart = () => {
				if (!pieContainer.value) return;
				d3.select(pieContainer.value).selectAll("*").remove();
				const container = d3.select(pieContainer.value);
				const containerWidth = pieContainer.value.clientWidth;
				const containerHeight = pieContainer.value.clientHeight;
				const size = containerHeight * 0.9;
				const radius = size / 2;
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
				const isSingleValue = props.fieldKey === "Inflation (CPI)";
				const processedData = isSingleValue
					? [
							{ ...pieData.value[0], color: colors[0], isMainValue: true },
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
						.style("font-size", "16px")
						.style("fill", "#000000");
				}
				if (!isSingleValue && pieData.value.length > 1) {
					const legend = svg.append("g").attr("class", "legend");
					const legendItemSize = 12;
					const legendSpacing = 4;
					const legendStartX = containerWidth / 2 - 110;
					const legendStartY = -containerHeight / 2 + 20;
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
							.attr("x", legendItemSize + 2)
							.attr("y", legendItemSize - 2)
							.text(`${d.name}: ${d.value.toFixed(1)}%`)
							.style("font-size", "12px")
							.style("fill", "#000000");
					});
				}
			};

			const renderBarChart = () => {
				if (!barContainer.value) return;
				d3.select(barContainer.value).selectAll("*").remove();
				const container = d3.select(barContainer.value);
				const [width, height] = [
					container.node().clientWidth,
					container.node().clientHeight
				];
				const margin = { top: 10, right: 10, bottom: 30, left: 10 };
				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${width} ${height}`);
				const maxYValue =
					(props.unifiedMax ??
						d3.max(simpleBarData.value, d => d.value) * 1.1) ||
					1;
				const minYValue = Math.min(
					0,
					d3.min(simpleBarData.value, d => d.value) || 0
				);
				const y = d3
					.scaleLinear()
					.domain([minYValue, maxYValue])
					.range([height - margin.bottom, margin.top]);
				const barCount = simpleBarData.value.length;
				const barWidth = Math.min(
					60,
					(width - margin.left - margin.right) / barCount - 10
				);
				const startX =
					(width -
						barCount * barWidth -
						(barCount > 1 ? (barCount - 1) * 10 : 0)) /
					2;
				svg
					.selectAll(".bar")
					.data(simpleBarData.value)
					.enter()
					.append("rect")
					.attr("x", (d, i) => startX + i * (barWidth + 10))
					.attr("y", d => y(Math.max(0, d.value)))
					.attr("width", barWidth)
					.attr("height", d => Math.abs(y(d.value) - y(0)))
					.attr("fill", (d, i) => colors[i % colors.length])
					.style("opacity", 0.8);
				svg
					.selectAll(".bar-label")
					.data(simpleBarData.value)
					.enter()
					.append("text")
					.attr("x", (d, i) => startX + i * (barWidth + 10) + barWidth / 2)
					.attr("y", height - 5)
					.attr("text-anchor", "middle")
					.attr("font-size", "10px")
					.attr("fill", "#000000")
					.text(d => formatNumber(d.value));
			};

			const renderLineChart = () => {
				if (!lineContainer.value || lineData.value.length === 0) return;
				d3.select(lineContainer.value).selectAll("*").remove();
				const container = d3.select(lineContainer.value);
				const [width, height] = [
					container.node().clientWidth,
					container.node().clientHeight
				];
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
					.domain(d3.extent(lineData.value, d => d.y))
					.range([height - margin.bottom, margin.top]);
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
				svg
					.selectAll(".dot")
					.data(lineData.value)
					.enter()
					.append("circle")
					.attr("cx", (d, i) => x(i))
					.attr("cy", d => y(d.y))
					.attr("r", 3)
					.attr("fill", "#3498db");
				svg
					.selectAll(".line-label")
					.data(lineData.value)
					.enter()
					.append("text")
					.attr("x", (d, i) => x(i))
					.attr("y", height - 5)
					.attr("text-anchor", "middle")
					.attr("font-size", "12px")
					.attr("fill", "#000000")
					.text(d => formatNumber(d.y));
			};

			const CATEGORY_COLORS = {
				Machinery: "#8dd3c7",
				"Mineral Fuels": "#ffffb3",
				"Integrated Circuits": "#bebada",
				"Vehicles and their parts": "#fb8072",
				Plastics: "#80b1d3",
				"Iron and Steel": "#fdb462",
				"Instruments and Apparatus": "#b3de69",
				"Organic Chemicals": "#fccde5",
				"Transport Equipment": "#bc80bd",
				"Electrical Machinery": "#ccebc5",
				Chemicals: "#ffed6f",
				"Manufactured Goods": "#d9d9d9",
				"Raw Materials": "#fdb462",
				Foodstuff: "#ffb347",
				Others: "#a9a9a9",
				Electronics: "#fdb462",
				telecommunications: "#b3de69",
				"automobile production": "#fccde5",
				shipbuilding: "#d9d9d9",
				steel: "#bc80bd",
				"High technology": "#ccebc5",
				"Motor vehicles": "#ffed6f",
				"Machine tools": "#8dd3c7",
				China: "#fb8072",
				"United States": "#80b1d3",
				ASEAN: "#fdb462",
				"European Union": "#b3de69",
				Taiwan: "#fccde5",
				Japan: "#d9d9d9",
				"South Korea": "#bc80bd"
			};

			const renderStackedChart = () => {
				if (!stackedContainer.value) return;

				const filteredData = processedField.value || [];
				if (filteredData.length === 0) {
					d3.select(stackedContainer.value).html(
						'<div class="no-data">-</div>'
					);
					return;
				}

				// 统一清理名称的函数
				const cleanCategoryName = name => {
					return String(name)
						.replace(/[.:\s]*$/, "") // 移除末尾的冒号、点和空格
						.replace(/^Others:?$/, "Others") // 统一 Others 和 Others: 为 Others
						.trim();
				};

				const isPurelyCategorical = filteredData.every(item => {
					const num = safeToNumber(item.value);
					const isRawNumeric =
						!isNaN(parseFloat(item.raw)) && isFinite(item.raw);
					return num === 0 && !isRawNumeric;
				});

				let stackData;

				if (isPurelyCategorical) {
					const categoryCount = filteredData.length;
					const equalShare = categoryCount > 0 ? 100 / categoryCount : 0;
					stackData = filteredData.map(item => {
						const cleanName = cleanCategoryName(item.label || item.raw);
						return {
							name: cleanName,
							value: equalShare,
							color: props.categoryColors[cleanName] || "#cccccc",
							parent: item.parent
						};
					});
				} else {
					stackData = filteredData
						.map(item => {
							const cleanName = cleanCategoryName(item.label || item.raw);
							return {
								name: cleanName,
								value: safeToNumber(item.value),
								color: props.categoryColors[cleanName] || "#cccccc",
								parent: item.parent,
								raw: item.raw
							};
						})
						.filter(d => d.value > 0);
				}

				if (stackData.length === 0) {
					d3.select(stackedContainer.value).html(
						'<div class="no-data">-</div>'
					);
					return;
				}

				d3.select(stackedContainer.value).selectAll("*").remove();
				const container = d3.select(stackedContainer.value);
				const width = container.node().clientWidth,
					height = container.node().clientHeight;
				const margin = { top: 20, right: 140, bottom: 20, left: 140 };
				if (width <= 0 || height <= 0) return;

				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${width} ${height}`);
				const y = d3
					.scaleLinear()
					.domain([0, 100])
					.range([height - margin.bottom, margin.top]);
				const x = d3
					.scaleBand()
					.domain([0])
					.range([margin.left, width - margin.right])
					.padding(0.4);

				let cumulative = 0;
				const segments = stackData.map(d => {
					const segment = {
						...d,
						y: y(cumulative + d.value),
						height: Math.abs(y(cumulative) - y(cumulative + d.value)),
						x: x(0),
						width: x.bandwidth()
					};
					cumulative += d.value;
					return segment;
				});

				svg
					.selectAll(".stack-bar")
					.data(segments)
					.enter()
					.append("rect")
					.attr("x", d => d.x)
					.attr("y", d => d.y)
					.attr("width", d => d.width)
					.attr("height", d => d.height)
					.attr("fill", d => d.color)
					.style("opacity", 0.8);

				if (!isPurelyCategorical) {
					svg
						.selectAll(".stack-label")
						.data(segments)
						.enter()
						.append("g")
						.attr("class", "stack-label")
						.each(function (d, i) {
							const g = d3.select(this);
							if (d.value < 0.1) return;

							const labelText = `${d.value.toFixed(1)}%`;
							const textEl = g
								.append("text")
								.attr("font-size", "11px")
								.attr("fill", "#000000")
								.text(labelText);
							const textWidth = textEl.node().getBBox().width;

							if (textWidth > d.width - 10 || d.height < 15) {
								textEl.remove();
								const isLeft = i % 2 === 0;
								const labelX = isLeft ? d.x - 5 : d.x + d.width + 5;
								const labelY = d.y + d.height / 2 + 3;

								g.append("line")
									.attr("x1", isLeft ? d.x : d.x + d.width)
									.attr("y1", d.y + d.height / 2)
									.attr("x2", isLeft ? labelX + 2 : labelX - 2)
									.attr("y2", labelY - 3)
									.attr("stroke", "#666")
									.attr("stroke-width", 1);
								g.append("text")
									.attr("x", labelX)
									.attr("y", labelY)
									.attr("text-anchor", isLeft ? "end" : "start")
									.attr("font-size", "9px")
									.attr("fill", "#000000")
									.text(labelText);
							} else {
								textEl
									.attr("x", d.x + d.width / 2)
									.attr("y", d.y + d.height / 2 + 3)
									.attr("text-anchor", "middle");
							}
						});
				}

				const legendItemHeight = 18,
					legendFontSize = 10;
				const legendLeftX = margin.left - 140,
					legendRightX = width - margin.right + 40,
					legendYStart = margin.top;

				// 合并相同的类别名称（特别是 Others）
				const uniqueStackData = [];
				const nameMap = new Map();

				stackData.forEach(item => {
					if (nameMap.has(item.name)) {
						// 如果已经有相同的名称，合并值
						const existing = nameMap.get(item.name);
						existing.value += item.value;
					} else {
						// 新的唯一名称
						const newItem = { ...item };
						uniqueStackData.push(newItem);
						nameMap.set(item.name, newItem);
					}
				});

				const leftLegend = uniqueStackData.slice(0, 5);
				const rightLegend = uniqueStackData.slice(5, 10);

				svg
					.selectAll(".legend-left")
					.data(leftLegend)
					.enter()
					.append("g")
					.attr(
						"transform",
						(d, i) =>
							`translate(${legendLeftX}, ${
								legendYStart + i * legendItemHeight
							})`
					)
					.each(function (d) {
						const g = d3.select(this);
						g.append("rect")
							.attr("width", 12)
							.attr("height", 12)
							.attr("fill", d.color)
							.style("opacity", 0.8);
						g.append("text")
							.attr("x", 14)
							.attr("y", 10)
							.attr("font-size", legendFontSize)
							.attr("fill", "#000000")
							.text(d.name);
					});
				svg
					.selectAll(".legend-right")
					.data(rightLegend)
					.enter()
					.append("g")
					.attr(
						"transform",
						(d, i) =>
							`translate(${legendRightX}, ${
								legendYStart + i * legendItemHeight
							})`
					)
					.each(function (d) {
						const g = d3.select(this);
						g.append("rect")
							.attr("width", 12)
							.attr("height", 12)
							.attr("fill", d.color)
							.style("opacity", 0.8);
						g.append("text")
							.attr("x", 20)
							.attr("y", 10)
							.attr("font-size", legendFontSize)
							.attr("fill", "#000000")
							.text(d.name);
					});
			};

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
			const formatNumber = value => {
				const num = Number(value);
				if (isNaN(num)) return "0";
				if (props.type === "percentage") return num.toFixed(1) + "%";
				if (num >= 100000000) return (num / 100000000).toFixed(2) + "亿";
				if (num >= 10000) return (num / 10000).toFixed(1) + "万";
				if (num >= 1000) return (num / 1000).toFixed(1) + "千";
				return num.toFixed(0);
			};

			const isValidPieData = computed(() => pieData.value.length > 0);
			const pieData = computed(() => {
				if (!processedField.value) return [];
				return processedField.value
					.map((item, index) => {
						let rawValue = item.raw || item.value || item;
						if (isYearEntry(String(rawValue))) return null;
						const value = safeToNumber(rawValue);
						if (value === 0 && isNaN(parseFloat(rawValue))) return null;
						let name = String(rawValue)
							.replace(/:?\s*\d+\.?\d*%?/g, "")
							.trim();
						if (isYearEntry(name)) return null;
						return {
							value: Math.min(100, Math.max(0, value)),
							name: name || "项目",
							index
						};
					})
					.filter(Boolean);
			});

			const formatSimpleText = value => {
				if (!value || value.length === 0) return "-";
				const items = value.map(
					item => item.raw || item.value || JSON.stringify(item)
				);
				return items.length > 3
					? items.slice(0, 3).join("; ") + "..."
					: items.join("; ");
			};

			const simpleBarData = computed(() => {
				if (!processedField.value) return [];
				return processedField.value
					.map(item => safeToNumber(item.value || item.raw))
					.filter(v => v !== 0 || !isYearEntry(String(v)))
					.map((v, index) => ({ value: v, index }));
			});

			const lineData = computed(() => {
				if (!processedField.value) return [];
				return processedField.value
					.filter(item => !isYearEntry(String(item.raw)))
					.map((item, index) => ({
						x: index,
						y: safeToNumber(item.value || item.raw)
					}));
			});

			const hasData = computed(
				() => processedField.value && processedField.value.length > 0
			);

			return {
				hoveredIndex,
				activeIndex,
				isTextHovered,
				pieContainer,
				barContainer,
				lineContainer,
				stackedContainer,
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
				processedField,
				getRawTextForRank
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
	.simple-text {
		text-align: center;
		font-size: 16px;
		word-break: break-word;
		padding: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
		border-radius: 4px;
		background-color: #f8f9fa;
		max-width: 100%;
		color: #000000;
	}
	.simple-text:hover {
		background-color: #e9ecef;
		transform: translateY(-2px);
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
	}
	.gdp-rank-direct-display {
		white-space: pre-wrap;
		text-align: center;
		font-size: 16px;
		line-height: 1.5;
		color: #000000;
		padding: 8px;
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
	.d3-chart-container {
		width: 100%;
		height: 160px;
		min-height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}
	.d3-tooltip {
		z-index: 10;
		white-space: nowrap;
		pointer-events: none;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
	}
	.no-data {
		color: #999;
		font-style: italic;
		padding: 10px;
	}
	.y-axis line {
		stroke: #e0e0e0;
		stroke-dasharray: 2, 2;
	}
	.y-axis text {
		font-size: 10px;
		fill: #666;
	}
	@media (max-width: 768px) {
		.simple-text {
			font-size: 14px;
		}
		.gdp-rank-direct-display {
			font-size: 14px;
		}
		.d3-chart-container {
			min-height: 60px;
		}
	}
	.bar-label,
	.line-label,
	.stack-label {
		font-family: Arial, sans-serif;
		pointer-events: none;
		user-select: none;
		color: #000000;
	}
	@media (max-width: 768px) {
		.bar-label,
		.line-label,
		.stack-label {
			font-size: 10px;
		}
	}
</style>
