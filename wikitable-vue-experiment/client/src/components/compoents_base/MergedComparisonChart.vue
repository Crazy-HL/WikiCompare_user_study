<template>
	<div class="merged-comparison">
		<div
			v-if="adaptiveTriggered"
			class="merged-scale-controls"
			role="group"
			aria-label="合并图表刻度模式">
			<button
				v-for="option in scaleModeOptions"
				:key="option.value"
				type="button"
				:class="{ active: selectedScaleMode === option.value }"
				:disabled="option.value === 'index' && !canUseMergedTrendIndex"
				@click="selectScaleMode(option.value)">
				{{ option.label }}
			</button>
		</div>
		<div v-if="mergedTrendText" class="merged-scale-note">
			{{ mergedTrendText }}
		</div>
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
		detectAdaptiveScale,
		trendChange,
		trendIndexPoints
	} = require("@/js/adaptiveChartScale");
	const {
		buildMergedAdaptiveState,
		buildMergedComparisonOption,
		linearScaleDecision
	} = require("@/js/mergedComparisonAdaptiveOptions");
	const {
		createChartRenderController
	} = require("@/js/chartRenderScheduler");

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

	const AXIS_SPLIT_NUMBER = 4;
	const chartEl = ref(null);
	const selectedScaleMode = ref("auto");
	const scaleDecision = ref(linearScaleDecision());
	const scaleModeOptions = [
		{ value: "auto", label: "自动优化" },
		{ value: "linear", label: "原始线性" },
		{ value: "index", label: "趋势指数" }
	];

	const merged = computed(() => buildMergedComparison(props.row, props.titles));
	const adaptiveState = ref(buildMergedAdaptiveState({ data: merged.value }));
	const adaptiveTriggered = computed(() => adaptiveState.value.adaptiveTriggered);
	const canUseMergedTrendIndex = computed(() =>
		adaptiveState.value.canUseTrendIndex &&
		merged.value.mode === "line" &&
		merged.value.series.every(series => trendIndexPoints(series.data).length > 0)
	);
	const emptyMergedChart = computed(() => {
		const data = merged.value;
		return (
			data.mode === "text" ||
			!data.series?.some(series =>
				series.data?.some(point => Number.isFinite(point.value))
			)
		);
	});
	const mergedTrendText = computed(() => {
		if (!adaptiveTriggered.value || merged.value.mode !== "line") return "";
		return merged.value.series
			.map(series => {
				const change = trendChange(series.data);
				if (change.absoluteChange === null) return "";
				if (change.percentChange === null) {
					return `${series.name}：绝对变化 ${formatAxis(
						change.absoluteChange,
						merged.value
					)}`;
				}
				const sign = change.percentChange > 0 ? "+" : "";
				return `${series.name}：${sign}${change.percentChange.toFixed(1)}%`;
			})
			.filter(Boolean)
			.join("；");
	});

	const selectScaleMode = value => {
		selectedScaleMode.value = value;
	};

	const gridForData = data => ({
		top: 48,
		left: 56,
		right: 28,
		bottom: data.categories.length > 4 && data.mode !== "stacked" ? 70 : 42,
		containLabel: true
	});

	const resetAdaptiveState = () => {
		scaleDecision.value = linearScaleDecision();
		adaptiveState.value = buildMergedAdaptiveState({
			data: merged.value,
			selectedScaleMode: selectedScaleMode.value,
			scaleDecision: scaleDecision.value
		});
	};

	const resetRenderState = () => {
		selectedScaleMode.value = "auto";
		resetAdaptiveState();
	};

	const requestFrame = callback =>
		typeof window !== "undefined" && typeof window.requestAnimationFrame === "function"
			? window.requestAnimationFrame(callback)
			: setTimeout(callback, 0);
	const cancelFrame = id => {
		if (typeof window !== "undefined" && typeof window.cancelAnimationFrame === "function") {
			window.cancelAnimationFrame(id);
		} else {
			clearTimeout(id);
		}
	};

	const renderController = createChartRenderController({
		nextTick,
		requestFrame,
		cancelFrame,
		eventTarget: typeof window !== "undefined" ? window : null,
		getElement: () => chartEl.value,
		isEmpty: () => emptyMergedChart.value,
		createChart: element => echarts.init(element),
		buildOption: () => {
			const data = merged.value;
			const grid = gridForData(data);
			const drawableHeight = Math.max(
				0,
				chartEl.value.clientHeight -
					Number(grid.top || 0) -
					Number(grid.bottom || 0)
			);
			const decision = detectAdaptiveScale({
				...(data.scaleContext || {}),
				drawableHeight
			});
			const previousTriggered = adaptiveState.value.adaptiveTriggered;
			scaleDecision.value = decision;
			const state = buildMergedAdaptiveState({
				data,
				selectedScaleMode: selectedScaleMode.value,
				scaleDecision: decision
			});
			adaptiveState.value = state;
			return {
				option: buildMergedComparisonOption({ data, state, grid }),
				layoutKey: state.adaptiveTriggered,
				layoutChanged: previousTriggered !== state.adaptiveTriggered
			};
		},
		reset: resetRenderState
	});

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

	onMounted(() => renderController.mount());

	watch(
		() => [props.row, props.titles],
		() => renderController.schedule({ reset: true }),
		{ deep: true }
	);

	watch(
		() => selectedScaleMode.value,
		() => renderController.schedule()
	);

	onUnmounted(() => renderController.destroy());
</script>

<style scoped>
	.merged-comparison {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 420px;
		box-sizing: border-box;
		color: #1f2937;
	}

	.merged-scale-controls {
		display: flex;
		justify-content: center;
		gap: 6px;
		margin-bottom: 8px;
	}

	.merged-scale-controls button {
		border: 1px solid #cbd5e1;
		border-radius: 999px;
		background: #ffffff;
		padding: 5px 11px;
		color: #475569;
		cursor: pointer;
		font-size: 12px;
		font-weight: 600;
	}

	.merged-scale-controls button.active {
		border-color: #2563eb;
		background: #eff6ff;
		color: #1d4ed8;
	}

	.merged-scale-controls button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}

	.merged-scale-note {
		margin: -2px 0 8px;
		color: #64748b;
		font-size: 12px;
		text-align: center;
	}

	.merged-chart {
		flex: 1 1 auto;
		width: 100%;
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
