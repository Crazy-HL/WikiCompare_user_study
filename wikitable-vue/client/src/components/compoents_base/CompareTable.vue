<template>
	<div class="compare-container">
		<div v-if="store.isLoading" class="initial-loading">
			<div class="loading-spinner"></div>
			<p>正在准备数据对比...</p>
		</div>

		<div v-else-if="!store.session" class="empty-state">
			输入两篇英文 Wikipedia 文章 URL 后开始比较。
		</div>

		<div v-else-if="!rows.length" class="empty-state">
			没有找到可对比属性。
		</div>

		<div v-else class="comparison-grid">
			<div class="header left-column">
				{{ articleTitle("left") }}
			</div>
			<div class="header middle-column">对比属性</div>
			<div class="header right-column">
				{{ articleTitle("right") }}
			</div>

			<template v-for="row in rows" :key="row.id">
				<div
					class="cell left-column"
					@mouseover="highlight(row.leftSourceIds)"
					@mouseout="clearHighlight"
					@click="showFullChart(row, 'left')">
					<SimpleChart
						:field="chartField(row, 'left')"
						:type="chartDataType(row)"
						:visualization="chartVisualization(row)"
						:fieldKey="row.label" />
				</div>

				<div
					class="cell middle-column"
					@mouseover="highlightBoth(row)"
					@mouseout="clearHighlight">
					<div class="field-name">{{ row.label }}</div>
					<div class="field-type">
						{{ row.dataType }} · {{ row.sourceKind }}
					</div>
					<div class="score">差异度 {{ formatScore(row.score) }}</div>
					<div class="icon-actions">
						<button class="icon-btn compare" title="对比分析" @click="emit('compareAttribute', row)">
							Compare
						</button>
						<button class="icon-btn merge" title="合并图表" @click="showCombinedChart(row)">
							Merge
						</button>
					</div>
				</div>

				<div
					class="cell right-column"
					@mouseover="highlight(row.rightSourceIds)"
					@mouseout="clearHighlight"
					@click="showFullChart(row, 'right')">
					<SimpleChart
						:field="chartField(row, 'right')"
						:type="chartDataType(row)"
						:visualization="chartVisualization(row)"
						:fieldKey="row.label" />
				</div>
			</template>
		</div>

		<div
			v-if="showFullChartModal"
			class="full-chart-modal"
			@click.self="closeFullChart">
			<div class="modal-content">
				<button class="close-btn" @click="closeFullChart">x</button>
				<h3>{{ currentChart.title }}</h3>
				<div class="chart-container">
					<FullChart
						:field="currentChart.data"
						:type="currentChart.type"
						:visualization="currentChart.visualization"
						:fieldKey="currentChart.fieldKey" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
	import { computed, ref } from "vue";
	import SimpleChart from "./SimpleChart.vue";
	import FullChart from "./FullChart.vue";
	import { sessionStore as store } from "@/js/sessionStore";

	defineProps({
		div1RawData: Object,
		div3RawData: Object
	});

	const emit = defineEmits(["compareAttribute"]);

	const rows = computed(() => store.session?.rankedRows || []);
	const showFullChartModal = ref(false);
	const currentChart = ref({
		title: "",
		data: [],
		type: "text",
		visualization: "text-only",
		fieldKey: ""
	});

	const articleTitle = side => store.session?.articles?.[side]?.title || side;

	const chartField = (row, side) => {
		const sideData = row.visualization?.[side] || {};
		if (Array.isArray(sideData.values) && sideData.values.length) {
			return sideData.values.map(value => ({
				...value,
				raw: value.year ? `${value.year}: ${value.value}` : String(value.value)
			}));
		}
		return sideData.raw || "-";
	};

	const chartVisualization = row => {
		const chartType = String(row.chartType || "").toLowerCase();
		const map = {
			bar: "bar-chart",
			scatter: "bar-chart",
			pie: "pie-chart",
			stacked: "stacked-chart",
			line: "line-chart",
			text: "text-only"
		};
		return map[chartType] || "text-only";
	};

	const chartDataType = row => {
		const dataType = String(row.dataType || "").toLowerCase();
		if (dataType === "proportional") return "percentage";
		if (["numerical", "trend", "ordinal"].includes(dataType)) return "number";
		return "text";
	};

	const formatScore = score => `${Math.round(Number(score || 0) * 100)}%`;

	const highlight = sourceIds => {
		store.highlight(sourceIds || []);
	};

	const highlightBoth = row => {
		store.highlight([...(row.leftSourceIds || []), ...(row.rightSourceIds || [])]);
	};

	const clearHighlight = () => {
		store.clearHighlight();
	};

	const showFullChart = (row, side) => {
		currentChart.value = {
			title: `${articleTitle(side)} - ${row.label}`,
			data: chartField(row, side),
			type: chartDataType(row),
			visualization: chartVisualization(row),
			fieldKey: row.label
		};
		showFullChartModal.value = true;
	};

	const showCombinedChart = row => {
		const leftValues = Array.isArray(chartField(row, "left"))
			? chartField(row, "left").map(item => ({ ...item, raw: `Left ${item.raw}` }))
			: [{ raw: `Left: ${chartField(row, "left")}` }];
		const rightValues = Array.isArray(chartField(row, "right"))
			? chartField(row, "right").map(item => ({ ...item, raw: `Right ${item.raw}` }))
			: [{ raw: `Right: ${chartField(row, "right")}` }];

		currentChart.value = {
			title: `合并图表 - ${row.label}`,
			data: [...leftValues, ...rightValues],
			type: chartDataType(row),
			visualization: chartVisualization(row),
			fieldKey: row.label
		};
		showFullChartModal.value = true;
	};

	const closeFullChart = () => {
		showFullChartModal.value = false;
	};
</script>

<style scoped>
	.compare-container {
		width: 100%;
		height: 100%;
		padding: 8px;
		box-sizing: border-box;
		position: relative;
	}

	.initial-loading,
	.empty-state {
		display: flex;
		min-height: 220px;
		align-items: center;
		justify-content: center;
		color: #64748b;
		text-align: center;
	}

	.initial-loading {
		flex-direction: column;
	}

	.loading-spinner {
		width: 30px;
		height: 30px;
		border: 3px solid #e2e8f0;
		border-top: 3px solid #2563eb;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.comparison-grid {
		display: grid;
		grid-template-columns: minmax(120px, 1fr) minmax(120px, 150px) minmax(120px, 1fr);
		width: 100%;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
	}

	.header {
		background: #f1f5f9;
		padding: 10px;
		font-weight: 600;
		text-align: center;
		border-bottom: 1px solid #e0e0e0;
		color: #334155;
	}

	.cell {
		min-height: 96px;
		padding: 8px;
		border-bottom: 1px solid #edf2f7;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.left-column {
		border-right: 1px solid #edf2f7;
	}

	.right-column {
		border-left: 1px solid #edf2f7;
	}

	.middle-column {
		flex-direction: column;
		gap: 5px;
		text-align: center;
		background: #fbfdff;
	}

	.field-name {
		font-size: 13px;
		font-weight: 600;
		color: #1e293b;
		overflow-wrap: anywhere;
	}

	.field-type,
	.score {
		font-size: 11px;
		color: #64748b;
	}

	.icon-actions {
		display: flex;
		gap: 6px;
		justify-content: center;
	}

	.icon-btn {
		border: 1px solid #cbd5e1;
		border-radius: 6px;
		background: white;
		color: #334155;
		font-size: 11px;
		padding: 3px 6px;
		cursor: pointer;
	}

	.icon-btn:hover {
		background: #eff6ff;
		border-color: #93c5fd;
		color: #1d4ed8;
	}

	.full-chart-modal {
		position: fixed;
		inset: 0;
		background: rgba(15, 23, 42, 0.45);
		z-index: 3000;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.modal-content {
		background: white;
		border-radius: 8px;
		width: min(760px, 90vw);
		max-height: 82vh;
		padding: 18px;
		position: relative;
		overflow: auto;
	}

	.close-btn {
		position: absolute;
		right: 10px;
		top: 10px;
		border: 0;
		background: #f1f5f9;
		border-radius: 999px;
		width: 28px;
		height: 28px;
		cursor: pointer;
	}

	.chart-container {
		min-height: 320px;
	}
</style>
