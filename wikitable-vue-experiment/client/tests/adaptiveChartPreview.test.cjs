const assert = require("assert");
const fs = require("fs");
const path = require("path");

const componentDir = path.join(__dirname, "..", "src", "components", "compoents_base");
const compareTableSource = fs.readFileSync(path.join(componentDir, "CompareTable.vue"), "utf8");
const simpleChartSource = fs.readFileSync(path.join(componentDir, "SimpleChart.vue"), "utf8");
const chartValueDisplaySource = fs.readFileSync(
	path.join(__dirname, "..", "src", "js", "chartValueDisplay.js"),
	"utf8"
);

assert(compareTableSource.includes("const adaptiveScaleContext = (row, { compactPreview = true } = {}) =>"));
assert(compareTableSource.includes(':side="\'left\'"'));
assert(compareTableSource.includes(':side="\'right\'"'));
assert(compareTableSource.includes(':scaleContext="adaptiveScaleContext(row)"'));
assert(compareTableSource.includes("normalizedRowPreviewValues(row)"));
assert(!compareTableSource.includes("Exchange rates"));

const chartFieldStart = compareTableSource.indexOf("const chartField = (row, side, compactPreview = false) => {");
const chartFieldEnd = compareTableSource.indexOf("const normalizedRowPreviewValues = row => {", chartFieldStart);
const chartFieldBody = compareTableSource.slice(chartFieldStart, chartFieldEnd);
assert(!chartFieldBody.includes("raw: value.display"));
assert(!chartFieldBody.includes("rawText: value.display"));
assert(chartValueDisplaySource.includes("originalDisplay"));

const adaptiveContextStart = compareTableSource.indexOf("const adaptiveScaleContext = (row, { compactPreview = true } = {}) =>");
const adaptiveContextEnd = compareTableSource.indexOf("const canMergeChart = row =>", adaptiveContextStart);
const adaptiveContextBody = compareTableSource.slice(adaptiveContextStart, adaptiveContextEnd);
assert(adaptiveContextBody.includes("const normalized = normalizedRowPreviewValues(row);"));
assert(adaptiveContextBody.includes("value.normalizedBaseValue"));
assert(adaptiveContextBody.includes('valueSpace: compactPreview ? "compact-preview" : "normalized-base"'));
assert(adaptiveContextBody.includes('decisionStatus: compactPreview ? "resolved" : "pending"'));
assert(adaptiveContextBody.includes("requiresActualHeightDecision: !compactPreview"));
assert.match(
	adaptiveContextBody,
	/decision:\s*compactPreview\s*\?\s*detectAdaptiveScale\(\{[\s\S]*?leftValues,[\s\S]*?rightValues,[\s\S]*?domain,[\s\S]*?drawableHeight:\s*PREVIEW_DRAWABLE_HEIGHT,[\s\S]*?visualization,[\s\S]*?\}\)\s*:\s*null/
);
assert.strictEqual(
	(adaptiveContextBody.match(/PREVIEW_DRAWABLE_HEIGHT/g) || []).length,
	1,
	"preview drawable height must only participate in the compact-preview decision"
);
assert(compareTableSource.includes("adaptiveScaleContext(row, { compactPreview: false })"));

assert(compareTableSource.includes("canonicalBaseChartItems"));
const canonicalFieldStart = compareTableSource.indexOf("const canonicalFullChartField = (row, side) =>");
const canonicalFieldEnd = compareTableSource.indexOf("const valueDisplayText =", canonicalFieldStart);
const canonicalFieldBody = compareTableSource.slice(canonicalFieldStart, canonicalFieldEnd);
assert(canonicalFieldBody.includes("normalizedRowPreviewValues(row)"));
assert(canonicalFieldBody.includes("canonicalBaseChartItems"));
const showFullChartStart = compareTableSource.indexOf("const showFullChart = (row, side) =>");
const showFullChartEnd = compareTableSource.indexOf("const showCombinedChart =", showFullChartStart);
const showFullChartBody = compareTableSource.slice(showFullChartStart, showFullChartEnd);
assert(showFullChartBody.includes("const scaleContext = adaptiveScaleContext(row, { compactPreview: false });"));
assert.match(
	showFullChartBody,
	/data:\s*scaleContext\?\.valueSpace === "normalized-base"\s*\? canonicalFullChartField\(row, side\)\s*:\s*chartField\(row, side\)/
);
assert(showFullChartBody.includes("scaleContext,"));

assert(simpleChartSource.includes("detectAdaptiveScale"));
assert(simpleChartSource.includes("adaptiveDomain"));
assert(simpleChartSource.includes("d3.scaleLog()"));
assert(simpleChartSource.includes("d3.scaleSymlog()"));
assert(simpleChartSource.includes('class="compressed-scale-badge"'));
assert(simpleChartSource.includes("由于共享线性坐标会使一侧图形不可见"));
assert(simpleChartSource.includes('.attr("class", "compressed-point")'));
assert(simpleChartSource.includes("trendChange(lineData.value"));
assert(simpleChartSource.includes("value: point.originalValue"));
assert(simpleChartSource.includes("originalDisplay: item.originalDisplay"));
assert(simpleChartSource.includes("originalValue:"));
assert(simpleChartSource.includes("originalDisplayText"));
assert(!simpleChartSource.includes("min-height: 3px"));
assert(!simpleChartSource.includes("Math.max(3, Math.abs(y(d.value) - y(0)))"));

const compressedStateStart = simpleChartSource.indexOf("const isCompressedScale = computed");
const compressedStateEnd = simpleChartSource.indexOf("const contextValues = computed", compressedStateStart);
const compressedStateBody = simpleChartSource.slice(compressedStateStart, compressedStateEnd);
assert(compressedStateBody.includes("hasData.value"));
assert(compressedStateBody.includes("hasValidScaleContext.value"));
assert(compressedStateBody.includes("supportsAdaptiveScale.value"));
assert(compressedStateBody.includes('activeScaleDecision.value.mode !== "linear"'));

assert(simpleChartSource.includes("const hasValidScaleContext = computed"));
assert(simpleChartSource.includes("const resetScaleDecision ="));
const watchStart = simpleChartSource.indexOf("onMounted(() => {");
const watchEnd = simpleChartSource.indexOf("const renderPieChart = () => {", watchStart);
const watchBody = simpleChartSource.slice(watchStart, watchEnd);
assert.match(
	watchBody,
	/if \(!hasData\.value \|\| !supportsAdaptiveScale\.value\)\s*\{\s*resetScaleDecision\(\);\s*\}/
);

const barStart = simpleChartSource.indexOf("const renderBarChart = () => {");
const barEnd = simpleChartSource.indexOf("const renderLineChart = () => {", barStart);
const barBody = simpleChartSource.slice(barStart, barEnd);
assert(barBody.includes("if (isCompressedScale.value)"));
assert(barBody.includes("renderCompressedPoints"));
assert(barBody.includes('.append("rect")'));
assert.match(
	barBody,
	/if \(!isCompressedScale\.value && minYValue < 0 && maxYValue > 0\)/
);
assert(
	(barBody.match(/originalDisplayText\(d\)/g) || []).length >= 2,
	"compressed bar tooltip and value label must both use original display text"
);

const lineStart = simpleChartSource.indexOf("const renderLineChart = () => {");
const lineEnd = simpleChartSource.indexOf("const renderStackedChart = () => {", lineStart);
const lineBody = simpleChartSource.slice(lineStart, lineEnd);
assert(
	(lineBody.match(/originalDisplayText\(d\)/g) || []).length >= 2,
	"compressed line tooltip and endpoint labels must both use original display text"
);

console.log("adaptiveChartPreview tests passed");
