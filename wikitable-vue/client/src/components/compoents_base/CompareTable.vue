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

		<div v-else class="comparison-grid" role="table">
			<div class="header left-column" role="columnheader">
				{{ articleTitle("left") }}
			</div>
			<div class="header middle-column" role="columnheader">对比属性</div>
			<div class="header right-column" role="columnheader">
				{{ articleTitle("right") }}
			</div>

			<template v-for="(row, index) in rows" :key="row.id">
				<div
					class="cell value-cell left-column"
					:title="detailText(row, 'left')"
					@mouseover="highlight(row.leftSourceIds)"
					@mouseout="clearHighlight"
					@click="showFullChart(row, 'left')">
					<SimpleChart
						:field="chartField(row, 'left')"
						:type="chartDataType(row)"
						:visualization="chartVisualization(row)"
						:fieldKey="row.label"
						:yDomain="barDomain(row)" />
				</div>

				<div
					class="cell middle-column meta-cell"
					@mouseover="highlightBoth(row)"
					@mouseout="clearHighlight">
					<div class="row-number">{{ index + 1 }}</div>
					<div class="field-name" :title="row.label">{{ row.label }}</div>
					<div class="meta-line">
						<span class="type-badge">{{ row.dataType }}</span>
						<span class="source-badge">{{ row.sourceKind }}</span>
					</div>
					<div class="score-line" :title="`差异度 ${formatScore(row.score)}`">
						<span>差异度</span>
						<div class="score-track">
							<div class="score-fill" :style="{ width: formatScore(row.score) }"></div>
						</div>
						<strong>{{ formatScore(row.score) }}</strong>
					</div>
					<div class="icon-actions">
						<button
							class="icon-btn compare"
							title="对比分析"
							aria-label="对比分析"
							@click.stop="emit('compareAttribute', row)">
							<font-awesome-icon :icon="['fas', 'align-left']" />
						</button>
						<button
							class="icon-btn merge"
							title="合并图表"
							aria-label="合并图表"
							@click.stop="showCombinedChart(row)">
							<font-awesome-icon :icon="['fas', 'chart-bar']" />
						</button>
					</div>
				</div>

				<div
					class="cell value-cell right-column"
					:title="detailText(row, 'right')"
					@mouseover="highlight(row.rightSourceIds)"
					@mouseout="clearHighlight"
					@click="showFullChart(row, 'right')">
					<SimpleChart
						:field="chartField(row, 'right')"
						:type="chartDataType(row)"
						:visualization="chartVisualization(row)"
						:fieldKey="row.label"
						:yDomain="barDomain(row)" />
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
					<MergedComparisonChart
						v-if="currentChart.combined"
						:row="currentChart.row"
						:titles="currentChart.titles" />
					<FullChart
						v-else
						:field="currentChart.data"
						:type="currentChart.type"
						:visualization="currentChart.visualization"
						:fieldKey="currentChart.fieldKey" />
				</div>
				<div v-if="!currentChart.combined && currentChart.details.length" class="chart-details">
					<div
						v-for="(detail, index) in currentChart.details"
						:key="index"
						class="detail-row">
						<span class="detail-label">{{ detail.label }}</span>
						<span class="detail-value">{{ detail.value }}</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
	import { computed, ref } from "vue";
	import SimpleChart from "./SimpleChart.vue";
	import FullChart from "./FullChart.vue";
	import MergedComparisonChart from "./MergedComparisonChart.vue";
	import { sessionStore as store } from "@/js/sessionStore";
	const { barChartDomain, formatValueDisplay } = require("@/js/chartValueDisplay");

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
		fieldKey: "",
		details: [],
		combined: false,
		row: null,
		titles: {}
	});

	const articleTitle = side => store.session?.articles?.[side]?.title || side;

	const chartField = (row, side) => {
		const sideData = row.visualization?.[side] || {};
		if (Array.isArray(sideData.values) && sideData.values.length) {
			return sideData.values.map(value => ({
				...value,
				display: valueDisplayText(value, sideData.raw, row.dataType),
				raw: valueDisplayText(value, sideData.raw, row.dataType),
				label: value.label || valueDisplayText(value, sideData.raw, row.dataType)
			}));
		}
		return sideData.raw || "-";
	};

	const valueDisplayText = (value, sourceRaw = "", dataType = "") => {
		return formatValueDisplay(value, sourceRaw, dataType);
	};

	const chartVisualization = row => {
		const chartType = String(row.chartType || "").toLowerCase();
		if (chartType === "pie" && hasNonPartWholePercentage(row)) {
			return "bar-chart";
		}
		if (String(row.dataType || "").toLowerCase() === "proportional") {
			if (hasNonPartWholePercentage(row)) return "bar-chart";
			const valueCount = maxValueCount(row);
			if (valueCount <= 1) return "bar-chart";
			return valueCount <= 4 ? "pie-chart" : "stacked-chart";
		}
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

	const maxValueCount = row => {
		return Math.max(
			...["left", "right"].map(side => {
				const values = row.visualization?.[side]?.values;
				return Array.isArray(values) ? values.length : 0;
			})
		);
	};

	const hasNonPartWholePercentage = row => {
		if (String(row.dataType || "").toLowerCase() !== "proportional") return false;
		return ["left", "right"].some(side => {
			const values = row.visualization?.[side]?.values;
			if (!Array.isArray(values) || values.length !== 1) return false;
			const value = Number(values[0]?.value);
			return Number.isFinite(value) && (value < 0 || value > 100);
		});
	};

	const chartDataType = row => {
		const dataType = String(row.dataType || "").toLowerCase();
		if (dataType === "proportional") return "percentage";
		if (dataType === "trend" && rowHasPercentValues(row)) return "percentage";
		if (["numerical", "trend", "ordinal"].includes(dataType)) return "number";
		return "text";
	};

	const barDomain = row => {
		if (chartVisualization(row) !== "bar-chart") return null;
		const values = ["left", "right"].flatMap(side => {
			const sideValues = row.visualization?.[side]?.values;
			return Array.isArray(sideValues)
				? sideValues.map(value => Number(value.value)).filter(Number.isFinite)
				: [];
		});
		return values.length ? barChartDomain(values) : null;
	};

	const rowHasPercentValues = row => {
		return ["left", "right"].some(side => {
			const raw = row.visualization?.[side]?.raw;
			return raw !== null && raw !== undefined && String(raw).includes("%");
		});
	};

	const formatScore = score => `${Math.round(Number(score || 0) * 100)}%`;

	const rawText = (row, side) => {
		const raw = row.visualization?.[side]?.raw;
		if (raw === null || raw === undefined || raw === "") return "-";
		return String(raw);
	};

	const extractedValueText = (row, side) => {
		const sideData = row.visualization?.[side] || {};
		if (!Array.isArray(sideData.values) || !sideData.values.length) return "";
		return sideData.values
			.map(value => valueDisplayText(value, sideData.raw, row.dataType))
			.join("\n");
	};

	const detailRows = (row, side) => {
		const rows = [];
		const extracted = extractedValueText(row, side);
		if (extracted) {
			rows.push({ label: "标准化值", value: extracted });
		}
		const raw = rawText(row, side);
		if (raw !== "-") {
			rows.push({ label: "原始值", value: raw });
		}
		return rows;
	};

	const detailText = (row, side) => {
		const details = detailRows(row, side);
		return details.map(detail => `${detail.label}: ${detail.value}`).join("\n");
	};

	const highlight = sourceIds => {
		store.highlight(sourceIds || []);
	};

	const highlightBoth = row => {
		store.highlightAndReveal([...(row.leftSourceIds || []), ...(row.rightSourceIds || [])]);
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
			fieldKey: row.label,
			details: detailRows(row, side),
			combined: false,
			row: null,
			titles: {}
		};
		showFullChartModal.value = true;
	};

	const showCombinedChart = row => {
		currentChart.value = {
			title: `合并图表 - ${row.label}`,
			data: [],
			type: chartDataType(row),
			visualization: "merged-comparison",
			fieldKey: row.label,
			details: [],
			combined: true,
			row: {
				...row,
				mergeVisualization: chartVisualization(row)
			},
			titles: {
				left: articleTitle("left"),
				right: articleTitle("right")
			}
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
		padding: 0;
		box-sizing: border-box;
		position: relative;
		background: #ffffff;
		color: #1f2937;
	}

	.initial-loading,
	.empty-state {
		display: flex;
		min-height: 220px;
		align-items: center;
		justify-content: center;
		color: #64748b;
		font-size: 13px;
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
		grid-template-columns: minmax(0, 1fr) minmax(92px, 106px) minmax(0, 1fr);
		width: 100%;
		min-height: 100%;
		border: 0;
		background: #dfe7f1;
		gap: 1px;
	}

	.header {
		position: sticky;
		top: 0;
		z-index: 5;
		background: linear-gradient(180deg, #fbfdff 0%, #f1f5f9 100%);
		padding: 10px 8px;
		border-bottom: 1px solid #cfd8e5;
		box-shadow: 0 1px 0 rgba(255, 255, 255, 0.82) inset;
		font-weight: 750;
		text-align: center;
		color: #243447;
		font-size: 11px;
		line-height: 1.25;
		overflow-wrap: anywhere;
		min-width: 0;
	}

	.cell {
		min-width: 0;
		min-height: 124px;
		padding: 7px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		background: #ffffff;
		transition: background 0.16s ease, box-shadow 0.16s ease;
	}

	.value-cell {
		flex-direction: column;
		gap: 6px;
		cursor: zoom-in;
		background: #ffffff;
	}

	.value-cell:hover {
		background: #fbfdff;
		box-shadow: inset 0 0 0 2px rgba(56, 103, 168, 0.12);
	}

	.middle-column {
		position: relative;
		flex-direction: column;
		gap: 6px;
		text-align: center;
		background: #f7fafc;
	}

	.meta-cell {
		padding: 9px 6px;
		border-left: 1px solid rgba(226, 232, 240, 0.7);
		border-right: 1px solid rgba(226, 232, 240, 0.7);
	}

	.meta-cell:hover {
		background: #f1f6fb;
	}

	.row-number {
		position: absolute;
		top: 6px;
		left: 6px;
		display: grid;
		width: 18px;
		height: 18px;
		place-items: center;
		border-radius: 50%;
		background: #e8eef6;
		color: #4b5f76;
		font-size: 10px;
		font-weight: 750;
	}

	.field-name {
		max-width: 100%;
		padding: 0 18px;
		color: #172033;
		font-size: 11px;
		font-weight: 750;
		line-height: 1.25;
		overflow-wrap: anywhere;
	}

	.meta-line {
		display: flex;
		flex-wrap: wrap;
		gap: 5px;
		justify-content: center;
	}

	.type-badge,
	.source-badge {
		padding: 2px 6px;
		border-radius: 999px;
		font-size: 10px;
		line-height: 1.4;
		border: 1px solid transparent;
		font-weight: 650;
	}

	.type-badge {
		background: #eaf2fb;
		border-color: #c9d9eb;
		color: #2c5b8f;
	}

	.source-badge {
		background: #eef7ef;
		border-color: #cfe2d2;
		color: #4d783d;
	}

	.score-line {
		display: grid;
		grid-template-columns: auto 1fr auto;
		width: 100%;
		align-items: center;
		gap: 5px;
		color: #64748b;
		font-size: 11px;
	}

	.score-line strong {
		color: #334155;
		font-weight: 600;
	}

	.score-track {
		height: 5px;
		overflow: hidden;
		border-radius: 999px;
		background: #dde6ef;
	}

	.score-fill {
		height: 100%;
		border-radius: inherit;
		background: linear-gradient(90deg, #3867a8 0%, #5f8f3f 100%);
	}

	.icon-actions {
		display: flex;
		gap: 8px;
		justify-content: center;
		align-items: center;
	}

	.icon-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: 1px solid rgba(255, 255, 255, 0.75);
		border-radius: 50%;
		background: #3867a8;
		color: #ffffff;
		font-size: 11px;
		line-height: 1;
		padding: 0;
		cursor: pointer;
		box-shadow:
			0 1px 2px rgba(15, 23, 42, 0.12),
			0 4px 10px rgba(56, 103, 168, 0.18);
		transition: transform 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
	}

	.icon-btn:hover {
		background: #2f588f;
		transform: translateY(-1px);
		box-shadow:
			0 2px 5px rgba(15, 23, 42, 0.14),
			0 7px 14px rgba(56, 103, 168, 0.2);
	}

	.icon-btn.merge {
		background: #5f8f3f;
		box-shadow:
			0 1px 2px rgba(15, 23, 42, 0.12),
			0 4px 10px rgba(95, 143, 63, 0.18);
	}

	.icon-btn.merge:hover {
		background: #507c35;
	}

	.full-chart-modal {
		position: fixed;
		inset: 0;
		background: rgba(15, 23, 42, 0.5);
		z-index: 3000;
		display: flex;
		align-items: center;
		justify-content: center;
		backdrop-filter: blur(3px);
	}

	.modal-content {
		background: white;
		border: 1px solid rgba(226, 232, 240, 0.9);
		border-radius: 10px;
		width: min(980px, 92vw);
		max-height: 86vh;
		padding: 20px;
		position: relative;
		overflow: auto;
		box-shadow:
			0 18px 45px rgba(15, 23, 42, 0.22),
			0 2px 8px rgba(15, 23, 42, 0.1);
	}

	.modal-content h3 {
		margin: 0 36px 16px 0;
		color: #172033;
		font-size: 18px;
		line-height: 1.3;
		font-weight: 750;
	}

	.close-btn {
		position: absolute;
		right: 12px;
		top: 12px;
		border: 0;
		background: #f1f5f9;
		color: #334155;
		border-radius: 999px;
		width: 30px;
		height: 30px;
		cursor: pointer;
		font-size: 13px;
		font-weight: 700;
		transition: background 0.16s ease, transform 0.16s ease;
	}

	.close-btn:hover {
		background: #e2e8f0;
		transform: scale(1.04);
	}

	.chart-container {
		min-height: 360px;
	}

	.chart-details {
		display: grid;
		gap: 8px;
		margin-top: 12px;
		padding-top: 12px;
		border-top: 1px solid #e2e8f0;
	}

	.detail-row {
		display: grid;
		grid-template-columns: 76px 1fr;
		gap: 10px;
		align-items: start;
		color: #334155;
		font-size: 12px;
		line-height: 1.45;
	}

	.detail-label {
		color: #64748b;
		font-weight: 600;
	}

	.detail-value {
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}

	:deep(.simple-chart) {
		width: 100%;
		min-height: 58px;
	}

	:deep(.simple-text) {
		font-size: 12px;
		line-height: 1.35;
	}
</style>
