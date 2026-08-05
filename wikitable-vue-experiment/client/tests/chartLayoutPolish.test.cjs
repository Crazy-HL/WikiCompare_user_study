const assert = require("assert");
const fs = require("fs");
const path = require("path");

const simpleChartSource = fs.readFileSync(
  path.join(__dirname, "..", "src", "components", "compoents_base", "SimpleChart.vue"),
  "utf8"
);
const fullChartSource = fs.readFileSync(
  path.join(__dirname, "..", "src", "components", "compoents_base", "FullChart.vue"),
  "utf8"
);
const { buildFullChartBarOption } = require("../src/js/fullChartAdaptiveOptions");
const {
  buildMergedAdaptiveState,
  buildMergedComparisonOption,
} = require("../src/js/mergedComparisonAdaptiveOptions");

const singleFull = buildFullChartBarOption({
  data: [{ value: 128, display: "128", label: "Spending" }],
  drawableHeight: 320,
  chartHeight: 420,
  fieldKey: "Spending",
});
assert(
  singleFull.option.series[0].barMaxWidth <= 30,
  "Expanded single-value bar charts should use a narrow paper-like bar instead of filling the modal width"
);

const mergedSingle = {
  mode: "single",
  categories: ["Value"],
  yDomain: [0, 200],
  series: [
    { name: "Left", data: [{ value: 120, display: "120" }] },
    { name: "Right", data: [{ value: 160, display: "160" }] },
  ],
};
const mergedState = buildMergedAdaptiveState({ data: mergedSingle });
const mergedOption = buildMergedComparisonOption({ data: mergedSingle, state: mergedState, grid: {} });
assert(
  mergedOption.series.every(series => series.barMaxWidth <= 30),
  "Merged single-value bar charts should keep each bar narrow enough for comparison"
);

assert(
  simpleChartSource.includes("const previewSingleBarFill = 0.42") &&
    simpleChartSource.includes("const previewSingleBarMaxWidth = 54"),
  "Thumbnail single-value bars should be capped to a narrow width rather than using most of the cell"
);

assert(
  fullChartSource.includes("const pieLegendNames = seriesData.filter(item => !item.silent).map(item => item.name)") &&
    fullChartSource.includes("legend: [") &&
    fullChartSource.includes('orient: "vertical"') &&
    fullChartSource.includes("left: 8") &&
    fullChartSource.includes("right: 8") &&
    !fullChartSource.includes('orient: "horizontal",\n\t\t\t\t\tleft: "center",\n\t\t\t\t\tbottom: 0'),
  "Expanded pie charts should move legends to left/right side columns so bottom legends are not clipped"
);

assert(
  simpleChartSource.includes("const sidePieLegendGroups") &&
    simpleChartSource.includes("pie-legend-line") &&
    simpleChartSource.includes("const sidePieLegendX") &&
    !simpleChartSource.includes("const legendStartY = Math.max(\n\t\t\t\t\t\t\tcenterY + radius + 8"),
  "Pie thumbnails should use side legends with leader lines, not bottom legends that can be cut off"
);

console.log("chartLayoutPolish tests passed");
