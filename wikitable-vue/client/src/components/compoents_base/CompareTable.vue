<template>
	<div class="compare-container">
		<div v-if="store.isLoading" class="initial-loading">
			<div class="loading-spinner"></div>
			<p>正在准备数据对比...</p>
		</div>

		<div v-else-if="!store.session" class="empty-state">
			输入两篇来源页面 URL 后开始比较。
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

			<div
				v-for="(row, index) in rows"
				:key="row.id"
				class="comparison-row"
				v-memo="[row, index]">
				<div
					class="cell value-cell left-column"
					:title="detailText(row, 'left')"
					@mouseover="highlightSide(row, 'left')"
					@mouseout="clearHighlight"
					@click="showFullChart(row, 'left')">
					<div v-if="isCreditRatingRow(row)" class="credit-rating-list credit-rating-list-left">
						<div
							v-for="pair in creditRatingPairs(row)"
							:key="`left-credit-${pair.agency}`"
							class="credit-agency-card"
							:class="{ 'is-empty': !pair.left.items.length }">
							<div class="credit-agency-name">{{ pair.agency }}</div>
							<div class="credit-chip-grid">
								<div
									v-for="item in pair.left.items"
									:key="`${pair.agency}-left-${item.label}`"
									class="credit-chip">
									<span>{{ item.label }}</span>
									<strong>{{ item.value }}</strong>
								</div>
								<div v-if="!pair.left.items.length" class="credit-empty">—</div>
							</div>
						</div>
					</div>
					<div
						v-else-if="shouldShowDisplayLines(row) && displayItems(row, 'left').length"
						class="comparison-value-list comparison-value-list-left">
						<div
							v-for="item in displayItems(row, 'left')"
							:key="`left-display-${item.key}`"
							class="comparison-value-line"
							:class="displayLineClasses(item)"
							:title="displayLineText(item)">
							<span
								v-if="item.label"
								class="comparison-value-label"
								:class="`color-${item.colorKey}`">{{ item.label }}:</span>
							<span class="comparison-value-text">{{ item.valueText || "—" }}</span>
						</div>
					</div>
					<SimpleChart
						v-else
						:field="chartField(row, 'left', true)"
						:type="chartDataType(row)"
						:visualization="chartVisualization(row)"
						:fieldKey="row.label"
						:yDomain="chartDomain(row)"
						:side="'left'"
						:scaleContext="adaptiveScaleContext(row)" />
					</div>

					<div
						class="cell middle-column meta-cell"
						@mouseover="highlightBoth(row)"
						@mouseout="clearHighlight"
						@click="togglePinnedHighlight(row, $event)">
					<div class="meta-click-zone">
						<div class="row-number">{{ index + 1 }}</div>
						<div class="field-name" :title="row.label">{{ row.label }}</div>
						<div class="meta-compact-line" :title="scoreTitle(row)">
							<span class="type-badge">{{ row.dataType }}</span>
							<span class="source-badge">{{ row.sourceKind }}</span>
						</div>
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
							:class="{ 'is-disabled': !canMergeChart(row) }"
							:disabled="!canMergeChart(row)"
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
					@mouseover="highlightSide(row, 'right')"
					@mouseout="clearHighlight"
					@click="showFullChart(row, 'right')">
					<div v-if="isCreditRatingRow(row)" class="credit-rating-list credit-rating-list-right">
						<div
							v-for="pair in creditRatingPairs(row)"
							:key="`right-credit-${pair.agency}`"
							class="credit-agency-card"
							:class="{ 'is-empty': !pair.right.items.length }">
							<div class="credit-agency-name">{{ pair.agency }}</div>
							<div class="credit-chip-grid">
								<div
									v-for="item in pair.right.items"
									:key="`${pair.agency}-right-${item.label}`"
									class="credit-chip">
									<span>{{ item.label }}</span>
									<strong>{{ item.value }}</strong>
								</div>
								<div v-if="!pair.right.items.length" class="credit-empty">—</div>
							</div>
						</div>
					</div>
					<div
						v-else-if="shouldShowDisplayLines(row) && displayItems(row, 'right').length"
						class="comparison-value-list comparison-value-list-right">
						<div
							v-for="item in displayItems(row, 'right')"
							:key="`right-display-${item.key}`"
							class="comparison-value-line"
							:class="displayLineClasses(item)"
							:title="displayLineText(item)">
							<span
								v-if="item.label"
								class="comparison-value-label"
								:class="`color-${item.colorKey}`">{{ item.label }}:</span>
							<span class="comparison-value-text">{{ item.valueText || "—" }}</span>
						</div>
					</div>
					<SimpleChart
						v-else
						:field="chartField(row, 'right', true)"
						:type="chartDataType(row)"
						:visualization="chartVisualization(row)"
						:fieldKey="row.label"
						:yDomain="chartDomain(row)"
						:side="'right'"
						:scaleContext="adaptiveScaleContext(row)" />
				</div>
			</div>
		</div>

		<div
			v-if="showFullChartModal"
			class="full-chart-modal"
			@click.self="closeFullChart">
			<div class="modal-content">
				<button class="close-btn" @click="closeFullChart">x</button>
				<h3>{{ currentChart.title }}</h3>
				<div class="chart-container">
					<div
						v-if="isFullChartPending"
						class="chart-loading"
						role="status"
						aria-label="正在加载完整图表">
						<div class="chart-loading-surface"></div>
					</div>
					<MergedComparisonChart
						v-else-if="currentChart.combined"
						:row="currentChart.row"
						:titles="currentChart.titles" />
					<FullChart
						v-else
						:field="currentChart.data"
						:type="currentChart.type"
						:visualization="currentChart.visualization"
						:fieldKey="currentChart.fieldKey"
						:side="currentChart.side"
						:scaleContext="currentChart.scaleContext" />
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
	const {
		barChartDomain,
		canonicalBaseChartItems,
		formatValueDisplay,
		normalizePreviewChartItems,
	} = require("@/js/chartValueDisplay");
	const {
		PREVIEW_DRAWABLE_HEIGHT,
		detectAdaptiveScale,
	} = require("@/js/adaptiveChartScale");
	const {
		buildCreditRatingPairs,
		isCreditRatingRow,
	} = require("@/js/creditRatingDisplay");
	const { buildComparisonDisplayPlan } = require("@/js/comparisonDisplayPlan");

	defineProps({
		div1RawData: Object,
		div3RawData: Object
	});

	const emit = defineEmits(["compareAttribute"]);

	const rows = computed(() => store.session?.rankedRows || []);
	const showFullChartModal = ref(false);
	const isFullChartPending = ref(false);
	const currentChart = ref({
		title: "",
		data: [],
		type: "text",
		visualization: "text-only",
		fieldKey: "",
		details: [],
		combined: false,
		row: null,
		titles: {},
		scaleContext: null,
		side: ""
	});
	let fullChartRenderToken = 0;

	const emptyChartState = title => ({
		title,
		data: [],
		type: "text",
		visualization: "text-only",
		fieldKey: "",
		details: [],
		combined: false,
		row: null,
		titles: {},
		scaleContext: null,
		side: ""
	});

	const deferFullChartRender = callback => {
		if (
			typeof window !== "undefined" &&
			typeof window.requestAnimationFrame === "function"
		) {
			window.requestAnimationFrame(() => {
				window.requestAnimationFrame(callback);
			});
			return;
		}
		setTimeout(callback, 0);
	};

	const articleTitle = side => store.session?.articles?.[side]?.title || side;

	const chartField = (row, side, compactPreview = false) => {
		const sideData = row.visualization?.[side] || {};
		if (Array.isArray(sideData.values) && sideData.values.length) {
			if (compactPreview) {
				return normalizedRowPreviewValues(row)
					.filter(value => value.side === side)
					.map(({ side: _side, sourceIndex: _sourceIndex, ...value }) => value);
			}
			return sideData.values.map(value => ({
				...value,
				display: valueDisplayText(value, sideData.raw, row.dataType),
				raw: value.rawText || value.raw || valueDisplayText(value, sideData.raw, row.dataType),
				label: value.label
			}));
		}
		return sideData.raw || "-";
	};

	const normalizedRowPreviewValues = row => {
		const entries = ["left", "right"].flatMap(side => {
			const sideData = row.visualization?.[side] || {};
			const values = Array.isArray(sideData.values) ? sideData.values : [];
			return values.map((value, sourceIndex) => {
				const display = valueDisplayText(value, sideData.raw, row.dataType);
				return {
					...value,
					side,
					sourceIndex,
					display,
					raw: value.rawText || value.raw || display,
					label: value.label,
				};
			});
		});
		return normalizePreviewChartItems(entries, chartDataType(row));
	};

	const canonicalFullChartField = (row, side) => {
		const normalized = normalizedRowPreviewValues(row)
			.filter(value => value.side === side)
			.map(({ side: _side, sourceIndex: _sourceIndex, ...value }) => value);
		return canonicalBaseChartItems(normalized);
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
			if (hasNonPartWholePercentage(row)) {
				return rowHasYearSeries(row) ? "line-chart" : "bar-chart";
			}
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

	const creditRatingPairs = row => buildCreditRatingPairs(row);

	const displayPlan = row => buildComparisonDisplayPlan(row);

	const displayItems = (row, side) => displayPlan(row)[side] || [];

	const shouldShowDisplayLines = row => chartVisualization(row) === "text-only";

	const displayLineText = item => {
		if (!item?.label) return item?.valueText || "";
		return `${item.label}: ${item.valueText || "—"}`;
	};

	const displayLineClasses = item => ({
		"is-shared": item.shared,
		"is-single": item.colorKey === "single",
		"is-unmatched": !item.shared && item.colorKey !== "single",
	});

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
		const sides = ["left", "right"]
			.map(side => row.visualization?.[side]?.values)
			.filter(values => Array.isArray(values) && values.length);
		if (!sides.length) return false;
		return !sides.every(values => isPartWholePercentageValues(values, row));
	};

	const isPartWholePercentageValues = (values, row) => {
		if (!Array.isArray(values) || values.length < 2 || valuesHaveYearSeries(values)) {
			return false;
		}
		if (isNonExhaustiveShareContext(row)) return false;
		const labels = values
			.map(value => normalizeLabel(value?.label))
			.filter(Boolean);
		if (new Set(labels).size < 2) return false;
		const numbers = values.map(value => Number(value?.value));
		if (
			numbers.some(value => !Number.isFinite(value) || value < 0 || value > 100)
		) {
			return false;
		}
		const total = numbers.reduce((sum, value) => sum + value, 0);
		return total >= 95 && total <= 105;
	};

	const normalizeLabel = label =>
		String(label || "")
			.trim()
			.toLowerCase()
			.replace(/\s+/g, " ");

	const isNonExhaustiveShareContext = row => {
		const context = [
			row?.label,
			row?.visualization?.left?.raw,
			row?.visualization?.right?.raw
		].join(" ").toLowerCase();
		if (!/\bpartners?\b/.test(context)) return false;
		const labels = ["left", "right"].flatMap(side => {
			const values = row?.visualization?.[side]?.values;
			return Array.isArray(values)
				? values.map(value => normalizeLabel(value?.label)).filter(Boolean)
				: [];
		});
		return !labels.some(label =>
			["other", "others", "remaining", "rest"].includes(label)
		);
	};

	const rowHasYearSeries = row =>
		["left", "right"].some(side => {
			const values = row.visualization?.[side]?.values;
			return valuesHaveYearSeries(values);
		});

	const valuesHaveYearSeries = values => {
		if (!Array.isArray(values) || values.length < 2) return false;
		const years = values
			.map(value => Number(value?.year))
			.filter(Number.isFinite);
		return new Set(years).size >= 2;
	};

	const chartDataType = row => {
		const dataType = String(row.dataType || "").toLowerCase();
		if (dataType === "proportional") return "percentage";
		if (dataType === "trend" && rowHasPercentValues(row)) return "percentage";
		if (["numerical", "trend", "ordinal"].includes(dataType)) return "number";
		return "text";
	};

	const chartDomain = row => {
		const visualization = chartVisualization(row);
		if (!["bar-chart", "line-chart"].includes(visualization)) return null;
		const values = normalizedRowPreviewValues(row)
			.map(value => Number(value.value))
			.filter(Number.isFinite);
		return sharedDomainForValues(values, visualization);
	};

	const lineChartDomain = values => {
		const nums = values.filter(Number.isFinite);
		if (!nums.length) return null;
		const min = Math.min(...nums);
		const max = Math.max(...nums);
		if (min === max) {
			const padding = Math.max(1, Math.abs(min) * 0.15);
			return [min - padding, max + padding];
		}
		const padding = (max - min) * 0.12;
		return [min - padding, max + padding];
	};

	const sharedDomainForValues = (values, visualization) => {
		const numbers = values.map(Number).filter(Number.isFinite);
		if (!numbers.length) return null;
		return visualization === "line-chart"
			? lineChartDomain(numbers)
			: barChartDomain(numbers);
	};

	const adaptiveScaleContext = (row, { compactPreview = true } = {}) => {
		const visualization = chartVisualization(row);
		if (!["bar-chart", "line-chart"].includes(visualization)) return null;
		const normalized = normalizedRowPreviewValues(row);
		const valuesForSide = side => {
			return normalized
				.filter(value => value.side === side)
				.map(value =>
					Number(compactPreview ? value.value : value.normalizedBaseValue)
				)
				.filter(Number.isFinite);
		};
		const leftValues = valuesForSide("left");
		const rightValues = valuesForSide("right");
		const domain = sharedDomainForValues(
			[...leftValues, ...rightValues],
			visualization
		);
		if (!domain) return null;
		return {
			leftValues,
			rightValues,
			domain,
			visualization,
			valueSpace: compactPreview ? "compact-preview" : "normalized-base",
			decisionStatus: compactPreview ? "resolved" : "pending",
			requiresActualHeightDecision: !compactPreview,
			decision: compactPreview
				? detectAdaptiveScale({
						leftValues,
						rightValues,
						domain,
						drawableHeight: PREVIEW_DRAWABLE_HEIGHT,
						visualization,
					})
				: null,
		};
	};

	const canMergeChart = row => {
		if (chartVisualization(row) === "text-only") return false;
		return ["left", "right"].every(side => {
			const values = row.visualization?.[side]?.values;
			return Array.isArray(values) && values.some(value => Number.isFinite(Number(value.value)));
		});
	};

	const rowHasPercentValues = row => {
		return ["left", "right"].some(side => {
			const raw = row.visualization?.[side]?.raw;
			return raw !== null && raw !== undefined && String(raw).includes("%");
		});
	};

	const formatScore = score => `${Math.round(Number(score || 0) * 100)}%`;

	const scoreTitle = row => {
		const rankScore = row.rankScore ?? row.score;
		return `排序差异度 ${formatScore(rankScore)}；原始差异度 ${formatScore(row.score)}`;
	};

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

	const highlightSide = (row, side) => {
		const primary = row[`${side}SourceIds`] || [];
		const related = row[`${side}RelatedSourceIds`] || [];
		store.highlight(primary, related);
	};

	const highlightBoth = row => {
		store.highlight(
			[...(row.leftSourceIds || []), ...(row.rightSourceIds || [])],
			[...(row.leftRelatedSourceIds || []), ...(row.rightRelatedSourceIds || [])]
		);
	};

	const rowHighlightKey = row =>
		row?.id || `${row?.label || ""}:${row?.leftKey || ""}:${row?.rightKey || ""}`;

	const rowPrimarySourceIds = row => [
		...(row.leftSourceIds || []),
		...(row.rightSourceIds || [])
	];

	const rowRelatedSourceIds = row => [
		...(row.leftRelatedSourceIds || []),
		...(row.rightRelatedSourceIds || [])
	];

	let pinnedMetaCell = null;

	const setPinnedMetaCell = (cell, pinned) => {
		if (pinnedMetaCell && pinnedMetaCell !== cell) {
			pinnedMetaCell.classList.remove("is-pinned");
		}
		if (!cell) {
			pinnedMetaCell = null;
			return;
		}
		cell.classList.toggle("is-pinned", pinned);
		pinnedMetaCell = pinned ? cell : null;
	};

	const togglePinnedHighlight = (row, event) => {
		const pinned = store.togglePinnedHighlight(
			rowHighlightKey(row),
			rowPrimarySourceIds(row),
			rowRelatedSourceIds(row)
		);
		setPinnedMetaCell(event?.currentTarget || null, pinned);
	};

	const clearHighlight = () => {
		store.clearHighlight();
	};

	const showFullChart = (row, side) => {
		const token = ++fullChartRenderToken;
		const title = `${articleTitle(side)} - ${row.label}`;
		currentChart.value = emptyChartState(title);
		showFullChartModal.value = true;
		isFullChartPending.value = true;
		deferFullChartRender(() => {
			if (token !== fullChartRenderToken || !showFullChartModal.value) return;
			const scaleContext = adaptiveScaleContext(row, { compactPreview: false });
			currentChart.value = {
				title,
				data: scaleContext?.valueSpace === "normalized-base"
					? canonicalFullChartField(row, side)
					: chartField(row, side),
				type: chartDataType(row),
				visualization: chartVisualization(row),
				fieldKey: row.label,
				details: detailRows(row, side),
				combined: false,
				row: null,
				titles: {},
				scaleContext,
				side
			};
			isFullChartPending.value = false;
		});
	};

	const showCombinedChart = row => {
		if (!canMergeChart(row)) return;
		fullChartRenderToken += 1;
		isFullChartPending.value = false;
		currentChart.value = {
			title: `合并图表 - ${row.label}`,
			data: [],
			type: chartDataType(row),
			visualization: "merged-comparison",
			fieldKey: row.label,
			details: [],
			combined: true,
			scaleContext: null,
			side: "",
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
		fullChartRenderToken += 1;
		isFullChartPending.value = false;
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
		grid-template-columns: minmax(150px, 1fr) minmax(82px, 96px) minmax(150px, 1fr);
		width: 100%;
		min-height: 100%;
		border: 0;
		background: #dfe7f1;
		gap: 1px;
	}

	.comparison-row {
		display: contents;
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
		word-break: normal;
	}

	.cell {
		min-width: 0;
		min-height: 96px;
		padding: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		background: #ffffff;
		transition: background 0.16s ease, box-shadow 0.16s ease;
	}

	.value-cell {
		flex-direction: column;
		gap: 4px;
		cursor: zoom-in;
		background: #ffffff;
		padding: 4px;
		justify-content: center;
	}

	.value-cell:hover {
		background: #fbfdff;
		box-shadow: inset 0 0 0 2px rgba(56, 103, 168, 0.12);
	}

	.middle-column {
		position: relative;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		text-align: center;
		background: #f7fafc;
	}

	.meta-cell {
		padding: 6px 4px;
		border-left: 1px solid rgba(226, 232, 240, 0.7);
		border-right: 1px solid rgba(226, 232, 240, 0.7);
		cursor: pointer;
		justify-content: center;
	}

	.meta-cell:hover {
		background: #f1f6fb;
	}

	.meta-cell.is-pinned {
		background: #edf5ff;
		box-shadow: inset 0 0 0 2px rgba(56, 103, 168, 0.24);
	}

	.meta-click-zone {
		display: contents;
	}

	.row-number {
		position: absolute;
		top: 5px;
		left: 5px;
		display: grid;
		width: 16px;
		height: 16px;
		place-items: center;
		border-radius: 3px;
		background: #e8eef6;
		color: #4b5f76;
		font-size: 9px;
		font-weight: 750;
	}

	.field-name {
		max-width: 100%;
		padding: 0 10px;
		color: #172033;
		font-size: 10.5px;
		font-weight: 750;
		line-height: 1.25;
		overflow-wrap: anywhere;
	}

	.meta-compact-line {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		justify-content: center;
		align-items: center;
		max-width: 100%;
	}

	.type-badge,
	.source-badge {
		padding: 1px 4px;
		border-radius: 3px;
		font-size: 9px;
		line-height: 1.25;
		border: 1px solid transparent;
		font-weight: 650;
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
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

	.icon-actions {
		display: flex;
		width: 100%;
		gap: 6px;
		justify-content: center;
		align-items: center;
	}

	.icon-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		border: 1px solid rgba(255, 255, 255, 0.75);
		border-radius: 4px;
		background: #3867a8;
		color: #ffffff;
		font-size: 9px;
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

	.icon-btn.is-disabled,
	.icon-btn:disabled {
		cursor: not-allowed;
		opacity: 0.38;
		transform: none;
		box-shadow: none;
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

	.chart-loading {
		display: flex;
		align-items: stretch;
		justify-content: stretch;
		min-height: 420px;
		border: 1px solid #dbe3ee;
		border-radius: 8px;
		background: #fbfdff;
		overflow: hidden;
	}

	.chart-loading-surface {
		width: 100%;
		background:
			linear-gradient(90deg, rgba(241, 245, 249, 0.3), rgba(226, 232, 240, 0.75), rgba(241, 245, 249, 0.3)),
			repeating-linear-gradient(0deg, transparent 0, transparent 51px, rgba(148, 163, 184, 0.18) 52px),
			repeating-linear-gradient(90deg, transparent 0, transparent 87px, rgba(148, 163, 184, 0.14) 88px);
		background-size: 220px 100%, auto, auto;
		animation: chartLoadingSweep 1s ease-in-out infinite;
	}

	@keyframes chartLoadingSweep {
		from { background-position: -220px 0, 0 0, 0 0; }
		to { background-position: 100% 0, 0 0, 0 0; }
	}

	.comparison-value-list {
		display: grid;
		width: 100%;
		gap: 5px;
		align-content: start;
	}

	.comparison-value-line {
		display: block;
		width: 100%;
		padding: 5px 7px;
		border-left: 2px solid #d5dfeb;
		border-radius: 5px;
		background: #fbfdff;
		color: #1f2937;
		font-size: 12px;
		font-weight: 560;
		line-height: 1.38;
		overflow-wrap: anywhere;
		box-sizing: border-box;
	}

	.comparison-value-line.is-single {
		border-left-color: transparent;
		background: transparent;
		padding-left: 1px;
		font-size: 13px;
		font-weight: 650;
	}

	.comparison-value-line.is-unmatched {
		background: #fcfcfd;
		color: #334155;
	}

	.comparison-value-label {
		margin-right: 4px;
		font-weight: 820;
	}

	.comparison-value-label[class*="color-shared-"] { color: #375f8f; }
	.comparison-value-label[class*="color-unmatched"] { color: #64748b; }
	.comparison-value-label.color-shared-0 { color: #2f6f9f; }
	.comparison-value-label.color-shared-1 { color: #7a5a12; }
	.comparison-value-label.color-shared-2 { color: #6b4fa3; }
	.comparison-value-label.color-shared-3 { color: #23745a; }
	.comparison-value-label.color-shared-4 { color: #9a4f54; }

	.comparison-value-text {
		font-weight: 610;
	}

	.comparison-value-list-left .comparison-value-line {
		border-left-color: rgba(56, 103, 168, 0.28);
	}

	.comparison-value-list-right .comparison-value-line {
		border-left-color: rgba(95, 143, 63, 0.28);
	}

	.credit-rating-list {
		display: grid;
		width: 100%;
		gap: 6px;
		align-content: center;
	}

	.credit-agency-card {
		display: grid;
		gap: 6px;
		padding: 7px;
		border: 1px solid #d9e2ee;
		border-radius: 7px;
		background: #ffffff;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
	}

	.credit-rating-list-left .credit-agency-card {
		border-left: 3px solid #3867a8;
	}

	.credit-rating-list-right .credit-agency-card {
		border-left: 3px solid #5f8f3f;
	}

	.credit-agency-name {
		color: #334155;
		font-size: 11px;
		font-weight: 800;
		line-height: 1.1;
		white-space: nowrap;
	}

	.credit-chip-grid {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
	}

	.credit-chip {
		display: inline-flex;
		max-width: 100%;
		align-items: center;
		gap: 4px;
		padding: 3px 5px;
		border: 1px solid #dbe4ef;
		border-radius: 5px;
		background: #f8fafc;
		line-height: 1;
	}

	.credit-chip span {
		color: #64748b;
		font-size: 9px;
		font-weight: 750;
	}

	.credit-chip strong {
		color: #111827;
		font-size: 11px;
		font-weight: 800;
		white-space: nowrap;
	}

	.credit-empty {
		color: #94a3b8;
		font-size: 12px;
		font-weight: 700;
	}

	:deep(.simple-chart) {
		width: 100%;
		min-height: 84px;
	}

	:deep(.simple-text) {
		font-size: 12px;
		line-height: 1.35;
	}

	@media (max-width: 1180px) {
		.comparison-grid {
			grid-template-columns: minmax(0, 1fr) minmax(72px, 82px) minmax(0, 1fr);
		}

		.header {
			padding: 8px 6px;
			font-size: 10.5px;
			line-height: 1.2;
		}

		.cell {
			padding: 4px;
		}

		.field-name {
			padding: 0 12px;
			font-size: 10.5px;
		}
	}

	@media (max-width: 760px) {
		.comparison-grid {
			grid-template-columns: minmax(0, 1fr) minmax(62px, 72px) minmax(0, 1fr);
		}

		.header {
			padding: 7px 4px;
			font-size: 10px;
		}

		.value-cell {
			padding: 4px;
		}

	}
</style>
