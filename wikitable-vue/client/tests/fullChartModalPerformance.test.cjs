const assert = require("assert");
const fs = require("fs");
const path = require("path");

const componentDir = path.join(
	__dirname,
	"..",
	"src",
	"components",
	"compoents_base"
);

const compareTableSource = fs.readFileSync(
	path.join(componentDir, "CompareTable.vue"),
	"utf8"
);
const fullChartSource = fs.readFileSync(
	path.join(componentDir, "FullChart.vue"),
	"utf8"
);

assert(
	compareTableSource.includes("isFullChartPending"),
	"Single-chart modal should track a pending state before mounting the full chart"
);
assert(
	compareTableSource.includes('class="chart-loading"') &&
		compareTableSource.includes("v-if=\"isFullChartPending\""),
	"Single-chart modal should render a lightweight loading state before FullChart mounts"
);
assert(
	compareTableSource.includes("deferFullChartRender") &&
		compareTableSource.includes("requestAnimationFrame"),
	"Single-chart modal should defer heavy chart work with requestAnimationFrame"
);

const showFullChartStart = compareTableSource.indexOf("const showFullChart = (row, side) => {");
assert(showFullChartStart >= 0, "CompareTable should define showFullChart");
const showFullChartEnd = compareTableSource.indexOf("const showCombinedChart", showFullChartStart);
const showFullChartBody = compareTableSource.slice(showFullChartStart, showFullChartEnd);

assert(
	showFullChartBody.indexOf("showFullChartModal.value = true") <
		showFullChartBody.indexOf("deferFullChartRender"),
	"Single-chart click should open the modal before scheduling full chart work"
);
assert(
	showFullChartBody.indexOf("isFullChartPending.value = true") <
		showFullChartBody.indexOf("chartField(row, side)"),
	"Single-chart click should enter pending state before computing full chart data"
);
assert(
	showFullChartBody.includes("fullChartRenderToken"),
	"Deferred single-chart work should be guarded so stale clicks cannot render old charts"
);
assert(
	compareTableSource.includes('class="comparison-row"') &&
		compareTableSource.includes('v-memo="[row, index]"'),
	"Comparison rows should be memoized so opening the modal does not rerender every visible chart"
);
assert(
	compareTableSource.includes(".comparison-row") &&
		compareTableSource.includes("display: contents"),
	"Memoized comparison row wrappers should preserve the existing three-column grid layout"
);

assert(
	fullChartSource.includes("scheduleRenderChart") &&
		fullChartSource.includes("cancelScheduledRender") &&
		fullChartSource.includes("requestAnimationFrame"),
	"FullChart should schedule ECharts rendering outside the mount/watch hot path"
);
assert(
	!fullChartSource.includes("nextTick(renderChart);"),
	"FullChart should not initialize ECharts directly in the next Vue tick"
);

console.log("fullChartModalPerformance tests passed");
