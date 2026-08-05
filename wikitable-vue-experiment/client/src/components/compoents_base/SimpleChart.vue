<template>
	<div class="simple-chart">
		<div
			v-if="isCompressedScale"
			class="compressed-scale-badge"
			title="由于共享线性坐标会使一侧图形不可见，当前使用共享压缩刻度。图中标签和悬浮提示仍为原始数值。">
			压缩刻度
		</div>
		<div v-if="compressedTrendText" class="compressed-trend-change">
			{{ compressedTrendText }}
		</div>
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
				<span
					v-for="(item, index) in previewTextItems(processedField)"
					:key="index"
					class="text-chip">
					{{ item }}
				</span>
			</div>
			<div v-if="isTextHovered && fieldKey !== 'GDP rank'" class="text-tooltip">
				点击查看详情
			</div>
		</template>

		<!-- 饼图 (D3实现) -->
		<template v-else-if="visualization === 'pie-chart'">
			<div
				v-if="hasData && isValidPieData"
				class="d3-chart-container pie-chart-container"
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
				<span
					v-for="(item, index) in previewTextItems(processedField)"
					:key="index"
					class="text-chip">
					{{ item }}
				</span>
			</div>
			<div v-if="isTextHovered" class="text-tooltip">点击查看详情</div>
		</template>
	</div>
</template>

<script>
	import { computed, ref, onMounted, watch, nextTick } from "vue";
	import * as d3 from "d3";
	const {
		barChartDomain,
		categoryLabelForPoint,
		compactMiddleText,
		displayTextForPoint,
		formatChartNumber,
		normalizePreviewChartItems,
		pieLegendLabelForPoint,
		shouldShowPreviewLabel,
		shortValueText,
		xLabelForPoint
	} = require("@/js/chartValueDisplay");
	const {
		CHART_COLORS,
		CHART_REMAINDER_COLOR,
		PAPER_PIE_COLORS,
		categoryColor
	} = require("@/js/chartTheme");
	const {
		SYMLOG_CONSTANT,
		adaptiveDomain,
		detectAdaptiveScale,
		trendChange,
	} = require("@/js/adaptiveChartScale");

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
			yDomain: {
				type: Array,
				default: null
			},
			categoryColors: {
				type: Object,
				default: () => ({})
			},
			side: {
				type: String,
				default: ""
			},
			scaleContext: {
				type: Object,
				default: null
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
			const activeScaleDecision = ref({
				mode: "linear",
				constrainedSide: null,
				reason: null,
				diagnostics: {},
			});
			const resetScaleDecision = (drawableHeight = 0) => {
				activeScaleDecision.value = {
					mode: "linear",
					constrainedSide: null,
					reason: null,
					diagnostics: { drawableHeight },
				};
			};
			const supportsAdaptiveScale = computed(() =>
				["bar-chart", "line-chart"].includes(props.visualization)
			);
			const hasValidScaleContext = computed(() => {
				const context = props.scaleContext;
				if (!context || context.visualization !== props.visualization) return false;
				if (!Array.isArray(context.leftValues) || !Array.isArray(context.rightValues)) {
					return false;
				}
				if (
					!Array.isArray(context.domain) ||
					context.domain.length !== 2 ||
					!context.domain.every(value => Number.isFinite(Number(value))) ||
					Number(context.domain[0]) === Number(context.domain[1])
				) {
					return false;
				}
				return [...context.leftValues, ...context.rightValues].some(value =>
					Number.isFinite(Number(value))
				);
			});
			const isCompressedScale = computed(
				() =>
					hasData.value &&
					hasValidScaleContext.value &&
					supportsAdaptiveScale.value &&
					activeScaleDecision.value.mode !== "linear"
			);
			const contextValues = computed(() => [
				...(props.scaleContext?.leftValues || []),
				...(props.scaleContext?.rightValues || []),
			]);
			const activeDomain = computed(() =>
				adaptiveDomain(
					contextValues.value,
					activeScaleDecision.value.mode,
					props.scaleContext?.domain || props.yDomain
				)
			);
			const updateScaleDecision = (height, margin) => {
				const drawableHeight = Math.max(0, height - margin.top - margin.bottom);
				if (
					!hasData.value ||
					!supportsAdaptiveScale.value ||
					!hasValidScaleContext.value
				) {
					resetScaleDecision(drawableHeight);
					return;
				}
				activeScaleDecision.value = detectAdaptiveScale({
					leftValues: props.scaleContext.leftValues,
					rightValues: props.scaleContext.rightValues,
					domain: props.scaleContext.domain,
					drawableHeight,
					visualization: props.visualization,
				});
			};
			const compressedTrendText = computed(() => {
				if (!isCompressedScale.value || props.visualization !== "line-chart") {
					return "";
				}
				const change = trendChange(lineData.value.map(point => ({
					year: point.x,
					value: point.originalValue
				})));
				if (change.absoluteChange === null) return "";
				if (change.percentChange === null) {
					return `变化 ${formatNumber(change.absoluteChange)}`;
				}
				const sign = change.percentChange > 0 ? "+" : "";
				return `变化 ${sign}${change.percentChange.toFixed(1)}%`;
			});
			const createYScale = (domain, range) => {
				if (activeScaleDecision.value.mode === "log") {
					return d3.scaleLog().domain(domain).range(range).clamp(true);
				}
				if (activeScaleDecision.value.mode === "symlog") {
					return d3.scaleSymlog()
						.constant(SYMLOG_CONSTANT)
						.domain(domain)
						.range(range)
						.clamp(true);
				}
				return d3.scaleLinear().domain(domain).range(range);
			};

			const colors = CHART_COLORS;
			const paperPieColors = PAPER_PIE_COLORS;
			const remainderColor = CHART_REMAINDER_COLOR;

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

			const compactSvgText = (text, maxChars = 18) => {
				const value = String(text || "-").replace(/\s+/g, " ").trim();
				return value.length > maxChars ? `${value.slice(0, maxChars - 1)}…` : value;
			};

			const originalDisplayText = item => {
				const display = item?.originalDisplay ?? item?.fullDisplay ?? item?.display;
				if (display !== null && display !== undefined && String(display).trim()) {
					return String(display);
				}
				return formatNumber(item?.originalValue ?? item?.value ?? item?.y);
			};

			const previewTextAnchor = (index, total) => {
				if (total <= 1) return "middle";
				if (index === 0) return "start";
				if (index === total - 1) return "end";
				return "middle";
			};

			const previewMaxLabels = (width, desired = 3) => {
				const innerWidth = Math.max(0, Number(width) || 0);
				return Math.max(2, Math.min(desired, Math.floor(innerWidth / 54) || 2));
			};

			const previewHorizontalGap = (width, count) => {
				if (count <= 1) return 0;
				return Math.max(4, Math.min(8, width * 0.035));
			};

			const previewBarWidth = (width, margin, count) => {
				const safeCount = Math.max(1, count);
				const availableWidth = Math.max(12, width - margin.left - margin.right);
				const gap = previewHorizontalGap(width, safeCount);
				const previewSingleBarFill = 0.72;
				const previewSingleBarMaxWidth = 112;
				const maxBySpace =
					safeCount === 1
						? availableWidth * previewSingleBarFill
						: (availableWidth - gap * (safeCount - 1)) / safeCount;
				const maxByDensity =
					safeCount === 1 ? previewSingleBarMaxWidth : safeCount === 2 ? 88 : 72;
				return Math.max(10, Math.min(maxByDensity, maxBySpace));
			};

			const previewLinePadding = (pointCount, width) => {
				if (pointCount <= 2) return 0.08;
				if (width < 150) return 0.1;
				return 0.12;
			};

			const previewStackSideGutter = width =>
				Math.min(58, Math.max(34, width * 0.28));

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
								parent: item.parent || null,
								year: item.year || null,
								display: item.display || item.raw || item.value,
								originalDisplay: item.originalDisplay ?? item.display ?? item.rawText ?? item.raw,
								rawText: item.rawText || null,
								unit: item.unit || null,
								normalizedBaseValue: item.normalizedBaseValue,
								previewDivisor: item.previewDivisor,
								stripPreviewUnit: item.stripPreviewUnit === true
							};
						}
						return {
							raw: String(item),
							value: item,
							label: String(item),
							parent: null,
							year: null,
							display: String(item)
						};
					})
					.filter(
						item =>
							item.raw &&
							String(item.raw).trim() !== "" &&
							!isYearEntry(String(item.raw))
					);
			});

			const normalizedPreviewField = computed(() =>
				normalizePreviewChartItems(processedField.value, props.type)
			);

			const getRawTextForRank = field => {
				if (!field || field.length === 0) return "-";
				return field.map(item => item.raw).join("\n");
			};

			onMounted(() => {
				watch(
					() => [
						processedField.value,
						props.visualization,
						props.unifiedMax,
						props.yDomain,
						props.scaleContext,
						props.side,
					],
					() => {
						if (!hasData.value || !supportsAdaptiveScale.value) {
							resetScaleDecision();
						}
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
				const radius = Math.max(
					24,
					Math.min(containerWidth * 0.42, containerHeight * 0.38, 62)
				);
				const centerY = Math.max(radius + 4, containerHeight * 0.34);
				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${containerWidth} ${containerHeight}`);
				const chart = svg
					.append("g")
					.attr("transform", `translate(${containerWidth / 2}, ${centerY})`);
				const isSingleValue =
					pieData.value.length === 1 && props.type === "percentage";
				const processedData = isSingleValue
					? [
							{
								...pieData.value[0],
								value: Math.min(100, Math.max(0, pieData.value[0].value)),
								displayValue: pieData.value[0].value,
								color: paperPieColors[0],
								isMainValue: true
							},
							{
								value: Math.max(0, 100 - Math.max(0, Math.min(100, pieData.value[0].value))),
								displayValue: Math.max(0, 100 - Math.max(0, Math.min(100, pieData.value[0].value))),
								name: "剩余",
								color: remainderColor,
								isRemainder: true,
								index: 1
							}
					  ]
					: pieData.value.map((d, i) => ({
							...d,
							color: d.color || paperPieColors[i % paperPieColors.length],
							isMainValue: true
					  }));
				const pie = d3
					.pie()
					.value(d => d.value)
					.sort(null);
				const arc = d3
					.arc()
					.innerRadius(0)
					.outerRadius(radius)
					.padAngle(0.012)
					.cornerRadius(1.5);
				const arcs = chart
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
					.style("opacity", d => (d.data.isRemainder ? 0.5 : 0.92))
					.style("stroke", "#ffffff")
					.style("stroke-width", 1.5)
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
								`${d.data.name}: ${(d.data.displayValue ?? d.data.value).toFixed(1)}${
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
							.style("opacity", d.data.isRemainder ? 0.5 : 0.92)
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
					chart
						.append("text")
						.attr("text-anchor", "middle")
						.attr("dy", ".3em")
						.text(
							`${trimPercent(pieData.value[0].value)}${
								props.type === "percentage" ? "%" : ""
							}`
						)
						.style("font-size", "10px")
						.style("font-weight", "700")
						.style("fill", "#111827");
					svg
						.append("text")
						.attr("x", containerWidth / 2)
						.attr("y", Math.min(containerHeight - 8, centerY + radius + 13))
						.attr("text-anchor", "middle")
						.style("font-size", "8px")
						.style("fill", "#475569")
						.text(pieData.value[0].name || "value");
				}
				if (!isSingleValue && pieData.value.length > 1) {
					const legend = svg.append("g").attr("class", "legend");
					const legendItemSize = 7;
					const legendSpacing = 4;
					const maxPieLegendItems = pieData.value.length;
					const legendColumns = maxPieLegendItems > 5 ? 2 : 1;
					const legendRows = Math.ceil(maxPieLegendItems / legendColumns);
					const legendColumnWidth = Math.max(72, (containerWidth - 12) / legendColumns);
					const legendStartX = 6;
					const legendStartY = Math.max(
						centerY + radius + 8,
						containerHeight - legendRows * (legendItemSize + legendSpacing) - 3
					);
					const legendData = pieData.value.slice(0, maxPieLegendItems);
					const legendItems = legend
						.selectAll(".pie-legend-dot")
						.data(legendData)
						.enter()
						.append("g")
						.attr("class", "pie-legend-item")
						.attr("transform", (d, i) => {
							const column = i % legendColumns;
							const row = Math.floor(i / legendColumns);
							return `translate(${legendStartX + column * legendColumnWidth}, ${
								legendStartY + row * (legendItemSize + legendSpacing)
							})`;
						});
					legendItems
						.append("circle")
						.attr("class", "pie-legend-dot")
						.attr("cx", legendItemSize / 2)
						.attr("cy", legendItemSize / 2)
						.attr("r", legendItemSize / 2)
						.attr("fill", (d, i) => d.color || paperPieColors[i % paperPieColors.length]);
					legendItems
						.append("text")
						.attr("x", legendItemSize + 3)
						.attr("y", legendItemSize)
						.text((d, i) => {
							const label = pieLegendLabelForPoint(d, i, { total: legendData.length, fallback: d.name });
							const valueText = formatChartNumber(d.displayValue ?? d.value, props.type);
							return compactMiddleText(`${label} ${valueText}`, legendColumns > 1 ? 15 : 22);
						})
						.style("font-size", "7.5px")
						.style("font-weight", "500")
						.style("fill", "#2d3e50");
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
				const margin = { top: 14, right: 8, bottom: 12, left: 8 };
				updateScaleDecision(height, margin);
				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${width} ${height}`);
				const [minYValue, maxYValue] =
					Array.isArray(props.yDomain) && props.yDomain.length === 2
						? props.yDomain
						: props.unifiedMax
							? [0, props.unifiedMax]
							: barChartDomain(simpleBarData.value.map(d => d.value));
				const renderDomain = isCompressedScale.value
					? activeDomain.value
					: [minYValue, maxYValue];
				const y = createYScale(renderDomain, [height - margin.bottom, margin.top]);
				if (!isCompressedScale.value && minYValue < 0 && maxYValue > 0) {
					svg
						.append("line")
						.attr("x1", margin.left)
						.attr("x2", width - margin.right)
						.attr("y1", y(0))
						.attr("y2", y(0))
						.attr("stroke", "#94a3b8")
						.attr("stroke-width", 1)
						.attr("stroke-dasharray", "3 2");
				}
				const barCount = simpleBarData.value.length;
				const barGap = previewHorizontalGap(width, barCount);
				const barWidth = previewBarWidth(width, margin, barCount);
				const startX =
					(width -
						barCount * barWidth -
						(barCount > 1 ? (barCount - 1) * barGap : 0)) /
					2;
				const renderCompressedBars = () => {
					const minCompressedBarHeight = 4;
					svg
						.selectAll(".compressed-bar")
						.data(simpleBarData.value)
						.enter()
						.append("rect")
						.attr("class", "compressed-bar")
						.attr("x", (d, i) => startX + i * (barWidth + barGap))
						.attr("y", d => {
							const zeroY = y(0);
							const valueY = y(d.value);
							return d.value >= 0
								? Math.min(valueY, zeroY - minCompressedBarHeight)
								: zeroY;
						})
						.attr("width", barWidth)
						.attr("height", d => {
							const barHeight = Math.abs(y(d.value) - y(0));
							return Math.max(minCompressedBarHeight, barHeight);
						})
						.attr("fill", (d, i) => colors[i % colors.length])
						.style("opacity", 0.8)
						.append("title")
						.text(d => originalDisplayText(d));
				};
				const compactBarLabelText = d => compactSvgText(d.display, 10);

				if (isCompressedScale.value) {
					renderCompressedBars();
				} else {
					svg
						.selectAll(".bar")
						.data(simpleBarData.value)
						.enter()
						.append("rect")
						.attr("x", (d, i) => startX + i * (barWidth + barGap))
						.attr("y", d => y(Math.max(0, d.value)))
						.attr("width", barWidth)
						.attr("height", d => Math.abs(y(d.value) - y(0)))
						.attr("fill", (d, i) => colors[i % colors.length])
						.style("opacity", 0.8);
				}
				svg
					.selectAll(".bar-value-label")
					.data(simpleBarData.value
						.map((item, index) => ({ ...item, index }))
						.filter(item =>
							shouldShowPreviewLabel(item.index, simpleBarData.value.length, width, {
								maxVisible: previewMaxLabels(width, 3)
							})
					))
					.enter()
					.append("text")
					.attr("class", "bar-value-label")
					.attr("x", d => startX + d.index * (barWidth + barGap) + barWidth / 2)
					.attr("y", d =>
						isCompressedScale.value
							? Math.max(8, y(d.value) - 6)
							: d.value >= 0
								? Math.max(8, y(d.value) - 5)
								: Math.min(height - 4, y(d.value) + 11)
					)
					.attr("text-anchor", "middle")
					.attr("font-size", "9px")
					.attr("fill", "#1f2937")
					.text(d =>
						isCompressedScale.value
							? compactSvgText(originalDisplayText(d), 10)
							: compactBarLabelText(d)
					);
			};

			const renderLineChart = () => {
				if (!lineContainer.value || lineData.value.length === 0) return;
				d3.select(lineContainer.value).selectAll("*").remove();
				const container = d3.select(lineContainer.value);
				const [width, height] = [
					container.node().clientWidth,
					container.node().clientHeight
				];
				const margin = { top: 14, right: 8, bottom: 12, left: 8 };
				updateScaleDecision(height, margin);
				const svg = container
					.append("svg")
					.attr("width", "100%")
					.attr("height", "100%")
					.attr("viewBox", `0 0 ${width} ${height}`);
				const x = d3
					.scalePoint()
					.domain(lineData.value.map(d => d.xLabel))
					.range([margin.left, width - margin.right])
					.padding(previewLinePadding(lineData.value.length, width));
				const yExtent =
					Array.isArray(props.yDomain) && props.yDomain.length === 2
						? props.yDomain
						: d3.extent(lineData.value, d => d.y);
				const yPadding =
					yExtent[0] === yExtent[1] ? Math.max(1, Math.abs(yExtent[0]) * 0.15) : 0;
				const linearDomain =
					Array.isArray(props.yDomain) && props.yDomain.length === 2
						? yExtent
						: [yExtent[0] - yPadding, yExtent[1] + yPadding];
				const renderDomain = isCompressedScale.value ? activeDomain.value : linearDomain;
				const y = createYScale(renderDomain, [height - margin.bottom, margin.top]);
				const line = d3
					.line()
					.x(d => x(d.xLabel))
					.y(d => y(d.y))
					.curve(d3.curveMonotoneX);
				svg
					.append("path")
					.datum(lineData.value)
					.attr("fill", "none")
					.attr("stroke", colors[0])
					.attr("stroke-width", 2)
					.attr("d", line);
				svg
					.selectAll(".dot")
					.data(lineData.value)
					.enter()
					.append("circle")
					.attr("cx", d => x(d.xLabel))
					.attr("cy", d => y(d.y))
					.attr("r", 3)
					.attr("fill", colors[0])
					.append("title")
					.text(d => originalDisplayText(d));
				if (isCompressedScale.value || lineData.value.length <= 5) {
					const labelData = lineData.value
						.map((item, index) => ({ ...item, index }))
						.filter(item =>
							isCompressedScale.value
								? item.index === 0 || item.index === lineData.value.length - 1
								: shouldShowPreviewLabel(item.index, lineData.value.length, width, {
										maxVisible: previewMaxLabels(width, 2)
									})
						);
					svg
						.selectAll(".line-value-label")
						.data(labelData)
						.enter()
						.append("text")
						.attr("class", "line-value-label")
						.attr("x", d => x(d.xLabel))
						.attr("y", d => Math.max(8, y(d.y) - 6))
						.attr("text-anchor", d => previewTextAnchor(d.index, lineData.value.length))
						.attr("font-size", "8px")
						.attr("fill", "#1f2937")
						.text(d =>
							compactSvgText(
								isCompressedScale.value ? originalDisplayText(d) : d.display,
								12
							)
						);
				}
			};

			const renderStackedChart = () => {
				if (!stackedContainer.value) return;

				const filteredData = normalizedPreviewField.value || [];
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
					stackData = filteredData.map((item, index) => {
						const cleanName = cleanCategoryName(item.label || item.raw);
							return {
								name: cleanName,
								value: equalShare,
								display: `${trimPercent(equalShare)}%`,
								color: categoryColor(cleanName, index, props.categoryColors),
								parent: item.parent
							};
					});
				} else {
					stackData = filteredData
						.map((item, index) => {
							const cleanName = cleanCategoryName(item.label || item.raw);
							return {
								name: cleanName,
								value: safeToNumber(item.value),
								color: categoryColor(cleanName, index, props.categoryColors),
								parent: item.parent,
								raw: item.raw,
								display: previewDisplayText(item)
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

				const totalValue = stackData.reduce((sum, item) => sum + item.value, 0);
				const renderScale = totalValue > 101 ? totalValue : 100;
				stackData = stackData.map(item => ({
					...item,
					renderValue: renderScale ? (item.value / renderScale) * 100 : 0,
					displayValue: item.value
				}));

				d3.select(stackedContainer.value).selectAll("*").remove();
				const container = d3.select(stackedContainer.value);
				const width = container.node().clientWidth,
					height = container.node().clientHeight;
				if (width <= 0 || height <= 0) return;

				const svg = container
						.append("svg")
						.attr("width", "100%")
						.attr("height", "100%")
						.attr("viewBox", `0 0 ${width} ${height}`);

				const sideGutter = previewStackSideGutter(width);
				const margin = { top: 8, right: sideGutter, bottom: 8, left: sideGutter };
				const barAreaHeight = Math.max(36, height - margin.top - margin.bottom);
				const availableBarWidth = Math.max(14, width - margin.left - margin.right);
				const previewStackMaxBarWidth = 52;
				const barWidth = Math.min(
					previewStackMaxBarWidth,
					Math.max(18, availableBarWidth * 0.62)
				);
				const barX = (width - barWidth) / 2;
				const barBaseY = margin.top + barAreaHeight;
				const colorFor = (name, index) =>
					categoryColor(name, index, props.categoryColors);

				let cumulative = 0;
				const segments = stackData.map((d, index) => {
					const segmentHeight = (d.renderValue / 100) * barAreaHeight;
					const segment = {
						...d,
						x: barX,
						y: barBaseY - cumulative - segmentHeight,
						height: segmentHeight,
						width: barWidth,
						color: colorFor(d.name, index)
					};
					cumulative += segmentHeight;
					return segment;
				});

				svg
					.append("rect")
					.attr("x", barX)
					.attr("y", margin.top)
					.attr("width", barWidth)
					.attr("height", barAreaHeight)
					.attr("fill", "#f8fafc")
					.attr("stroke", "#e2e8f0")
					.attr("stroke-width", 1);

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
					.style("opacity", 0.9)
					.append("title")
					.text(d => `${d.name}: ${d.display || `${trimPercent(d.displayValue)}%`}`);

				if (!isPurelyCategorical) {
					svg
						.selectAll(".stack-label")
						.data(segments.filter(d => d.height >= 15 && d.displayValue >= 8))
						.enter()
						.append("text")
						.attr("class", "stack-label")
						.attr("x", d => d.x + d.width / 2)
						.attr("y", d => d.y + d.height / 2 + 3)
						.attr("text-anchor", "middle")
						.attr("font-size", "8px")
						.attr("fill", "#111827")
						.text(d => compactSvgText(d.display || `${trimPercent(d.displayValue)}%`, 8));
				}

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

				const legendItems = uniqueStackData.slice(0, 6);
				const splitIndex = Math.ceil(legendItems.length / 2);
				const sideLegendItems = [
						{ side: "left", items: legendItems.slice(0, splitIndex) },
						{ side: "right", items: legendItems.slice(splitIndex) }
					];
				const maxLegendChars = Math.max(4, Math.floor((sideGutter - 10) / 4.4));
				const legendStep = items =>
						items.length > 1
							? Math.min(14, Math.max(9, barAreaHeight / (items.length - 0.25)))
							: 0;

				sideLegendItems.forEach(group => {
						const items = group.items;
						const step = legendStep(items);
						const startY =
							items.length > 1
								? margin.top + Math.max(5, (barAreaHeight - step * (items.length - 1)) / 2)
								: margin.top + barAreaHeight / 2;
						svg
							.selectAll(`.stack-legend-${group.side}`)
							.data(items)
							.enter()
							.append("g")
							.attr("class", `stack-legend stack-legend-${group.side}`)
							.each(function (d, index) {
								const g = d3.select(this);
								const label = compactSvgText(d.name, maxLegendChars);
								const color = colorFor(d.name, legendItems.indexOf(d));
								const y = startY + index * step;
								const isLeft = group.side === "left";
								const x = isLeft ? barX - 7 : barX + barWidth + 7;
								const tickX = isLeft ? x + 2 : x - 2;
								const tickEndX = isLeft ? barX - 1 : barX + barWidth + 1;

								g.attr("transform", `translate(0, ${y})`);
								g.append("line")
									.attr("x1", tickX)
									.attr("x2", tickEndX)
									.attr("y1", 3)
									.attr("y2", 3)
									.attr("stroke", "#cbd5e1")
									.attr("stroke-width", 0.8);
								g.append("rect")
									.attr("x", isLeft ? x - 6 : x)
									.attr("y", 0)
									.attr("width", 6)
									.attr("height", 6)
									.attr("rx", 1.5)
									.attr("fill", color)
									.style("opacity", 0.9);
								g.append("text")
									.attr("x", isLeft ? x - 8 : x + 8)
									.attr("y", 6)
									.attr("text-anchor", isLeft ? "end" : "start")
									.attr("font-size", "7px")
									.attr("fill", "#334155")
									.text(label);
							});
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
				return formatChartNumber(value, props.type);
			};

			const trimPercent = value => {
				const num = Number(value);
				if (!Number.isFinite(num)) return "0";
				return num
					.toFixed(1)
					.replace(/\.0$/, "");
			};

			const isValidPieData = computed(() => pieData.value.length > 0);
				const pieData = computed(() => {
					if (!normalizedPreviewField.value) return [];
					return normalizedPreviewField.value
						.map((item, index) => {
						let rawValue = item.raw || item.value || item;
						if (isYearEntry(String(rawValue))) return null;
						const value = safeToNumber(item.value ?? rawValue);
						if (value === 0 && isNaN(parseFloat(rawValue))) return null;
						let name = pieLegendLabelForPoint(item, index, {
							fallback: props.fieldKey,
							total: normalizedPreviewField.value.length
						});
						if (isYearEntry(name)) return null;

						return {
							value,
							name,
							display: previewDisplayText(item),
							color: categoryColor(name, index, props.categoryColors),
							index
						};
					})
					.filter(Boolean);
			});

			const previewTextItems = value => {
				if (!value || value.length === 0) return ["-"];
				const items = value.map(item => displayTextForPoint(item));
				const visibleItems = items.slice(0, 3);
				if (items.length > 3) visibleItems.push(`+${items.length - 3}`);
				return visibleItems;
			};

			const formatSimpleText = value => previewTextItems(value).join("; ");

			const previewDisplayText = item =>
				item?.stripPreviewUnit ? item.unitlessDisplay : shortValueText(item, props.type);

			const simpleBarData = computed(() => {
				if (!normalizedPreviewField.value) return [];
				return normalizedPreviewField.value
					.map((item, index) => {
						const originalValue = Number(item.normalizedBaseValue);
						return {
							value: safeToNumber(item.value ?? item.raw),
							originalValue: Number.isFinite(originalValue)
								? originalValue
								: safeToNumber(item.value ?? item.raw),
							display: previewDisplayText(item),
							originalDisplay: item.originalDisplay,
							fullDisplay: displayTextForPoint(item),
							categoryLabel: categoryLabelForPoint(item, index, {
								fallback: props.fieldKey,
								total: normalizedPreviewField.value.length
							}),
							label: item.label,
							year: item.year,
							index
						};
					})
					.filter(item => item.value !== 0 || !isYearEntry(String(item.value)));
			});

			const lineData = computed(() => {
				if (!normalizedPreviewField.value) return [];
				return normalizedPreviewField.value
					.filter(item => !isYearEntry(String(item.raw)))
					.map((item, index) => {
						const originalValue = Number(item.normalizedBaseValue);
						return {
							x: item.year || index,
							xLabel: xLabelForPoint(item, index),
							y: safeToNumber(item.value ?? item.raw),
							originalValue: Number.isFinite(originalValue)
								? originalValue
								: safeToNumber(item.value ?? item.raw),
							display: previewDisplayText(item),
							originalDisplay: item.originalDisplay,
							fullDisplay: displayTextForPoint(item),
							label: item.label
						};
					});
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
				previewTextItems,
				hasData,
				isValidPieData,
				pieData,
				simpleBarData,
				lineData,
				normalizedPreviewField,
				isCompressedScale,
				compressedTrendText,
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
		font-family:
			Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
			"Segoe UI", sans-serif;
	}
	.compressed-scale-badge {
		position: absolute;
		top: 2px;
		right: 4px;
		z-index: 2;
		border: 1px solid #cbd5e1;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.94);
		padding: 1px 5px;
		color: #64748b;
		font-size: 9px;
		font-weight: 600;
		line-height: 1.4;
	}

	.compressed-trend-change {
		position: absolute;
		left: 4px;
		bottom: 1px;
		z-index: 2;
		color: #475569;
		font-size: 9px;
		font-weight: 600;
	}
	.simple-text {
		display: flex;
		width: 100%;
		max-width: 100%;
		flex-wrap: wrap;
		align-items: center;
		justify-content: center;
		gap: 5px;
		padding: 6px;
		cursor: pointer;
		transition: all 0.2s ease;
		border: 1px solid #dbe3ee;
		border-radius: 7px;
		background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
		color: #243447;
	}
	.simple-text:hover {
		background: #fbfdff;
		transform: translateY(-1px);
		box-shadow: 0 2px 7px rgba(15, 23, 42, 0.08);
	}
	.text-chip {
		display: inline-flex;
		max-width: 100%;
		align-items: center;
		border: 1px solid #d6e0ea;
		border-radius: 999px;
		background: #f4f7fb;
		padding: 2px 7px;
		color: #334155;
		font-size: 11px;
		font-weight: 600;
		line-height: 1.35;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.gdp-rank-direct-display {
		white-space: pre-wrap;
		text-align: center;
		font-size: 12px;
		line-height: 1.5;
		color: #243447;
		padding: 7px 9px;
		border: 1px solid #dbe3ee;
		border-radius: 7px;
		background: #fbfdff;
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
		height: 84px;
		min-height: 76px;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}
	.pie-chart-container {
		height: 160px;
		min-height: 148px;
		align-items: stretch;
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
			min-height: 76px;
		}
		.pie-chart-container {
			min-height: 148px;
		}
	}
	.bar-value-label,
	.line-value-label,
	.stack-label {
		font-family: Arial, sans-serif;
		pointer-events: none;
		user-select: none;
		color: #000000;
	}
	@media (max-width: 768px) {
		.bar-value-label,
		.line-value-label,
		.stack-label {
			font-size: 10px;
		}
	}
</style>
