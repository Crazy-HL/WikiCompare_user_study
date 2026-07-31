const assert = require("assert");
const fs = require("fs");
const path = require("path");
const echarts = require("echarts");

const {
  buildAdaptiveChartState,
  buildFullChartBarOption,
  buildFullChartLineOption,
  contextValuesForSide,
  labelValueForParam,
  orderedLinePoints,
  tooltipLineForParam,
} = require("../src/js/fullChartAdaptiveOptions");

const fullChartSource = fs.readFileSync(
  path.join(__dirname, "..", "src", "components", "compoents_base", "FullChart.vue"),
  "utf8"
);

const fieldData = [
  {
    value: 10,
    year: 2022,
    label: "2022",
    display: "US$ 10 million",
    originalDisplay: "$10,000,000",
  },
  {
    value: 20,
    year: 2023,
    label: "2023",
    display: "US$ 20 million",
    originalDisplay: "$20,000,000",
  },
];
const positiveContext = {
  decisionStatus: "pending",
  valueSpace: "normalized-base",
  leftValues: [1, 1.5],
  rightValues: [1000, 2000],
  domain: [0, 2000],
};

const autoState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "auto",
  drawableHeight: 100,
});
assert.strictEqual(autoState.canonicalAdaptiveEnabled, true);
assert.strictEqual(autoState.decision.mode, "log");
assert.strictEqual(autoState.resolvedScaleMode, "log");
assert.deepStrictEqual(autoState.plotData.map(item => item.value), [1, 1.5]);
assert(autoState.rawDomain[0] > 0, "log domain must exclude zero");

const linearState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "linear",
  drawableHeight: 100,
});
assert.strictEqual(linearState.decision.mode, "log");
assert.strictEqual(linearState.resolvedScaleMode, "linear");
assert.deepStrictEqual(linearState.rawDomain, positiveContext.domain);

const indexState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "index",
  drawableHeight: 100,
});
assert.strictEqual(indexState.resolvedScaleMode, "index");
assert.deepStrictEqual(indexState.renderedData.map(item => item.value), [100, 150]);
assert.deepStrictEqual(indexState.rawDomain, [94, 156]);

const resizedState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "auto",
  drawableHeight: 20000,
});
assert.strictEqual(resizedState.decision.mode, "linear");
assert.strictEqual(resizedState.resolvedScaleMode, "linear");
assert.notStrictEqual(resizedState.decision.mode, autoState.decision.mode);

const missingYearPoints = [
  { value: 30, year: 2022, label: "first" },
  { value: 10, year: null, label: "missing" },
  { value: 20, year: 2020, label: "last" },
];
assert.deepStrictEqual(
  orderedLinePoints(missingYearPoints).map(item => item.label),
  ["first", "missing", "last"]
);
const missingYearState = buildAdaptiveChartState({
  data: missingYearPoints,
  scaleContext: {
    ...positiveContext,
    leftValues: [30, 10, 20],
  },
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "index",
  drawableHeight: 100,
});
assert.deepStrictEqual(missingYearState.orderedData.map(item => item.label), ["first", "missing", "last"]);
assert.deepStrictEqual(
  missingYearState.renderedData.map(item => Number(item.value.toFixed(3))),
  [100, 33.333, 66.667]
);

const invalidSideState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: positiveContext,
  side: "middle",
  visualization: "line-chart",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  localDomain: [8, 22],
});
assert.strictEqual(invalidSideState.canonicalAdaptiveEnabled, false);
assert.deepStrictEqual(invalidSideState.plotData.map(item => item.value), [10, 20]);
assert.strictEqual(invalidSideState.decision.mode, "linear");
assert.deepStrictEqual(invalidSideState.rawDomain, [8, 22]);

const invalidContextState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: { ...positiveContext, valueSpace: "raw" },
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  localDomain: [8, 22],
});
assert.strictEqual(invalidContextState.canonicalAdaptiveEnabled, false);
assert.deepStrictEqual(invalidContextState.plotData.map(item => item.value), [10, 20]);
assert.deepStrictEqual(invalidContextState.rawDomain, [8, 22]);

const assertLocalLinearFallback = scaleContext => {
  const state = buildAdaptiveChartState({
    data: fieldData,
    scaleContext,
    side: "left",
    visualization: "line-chart",
    selectedScaleMode: "auto",
    drawableHeight: 100,
    localDomain: [8, 22],
  });
  assert.strictEqual(state.canonicalAdaptiveEnabled, false);
  assert.deepStrictEqual(state.plotData.map(item => item.value), [10, 20]);
  assert.strictEqual(state.decision.mode, "linear");
  assert.deepStrictEqual(state.rawDomain, [8, 22]);
};

assertLocalLinearFallback({
  decisionStatus: "pending",
  valueSpace: "normalized-base",
  rightValues: [1000, 2000],
  domain: [0, 2000],
});
assertLocalLinearFallback({
  ...positiveContext,
  leftValues: [1],
});
const sparseLeftValues = [];
sparseLeftValues.length = fieldData.length;
sparseLeftValues[0] = 1;
assertLocalLinearFallback({
  ...positiveContext,
  leftValues: sparseLeftValues,
});
assertLocalLinearFallback({
  ...positiveContext,
  leftValues: [1, undefined],
});

assert.deepStrictEqual(
  contextValuesForSide(
    { valueSpace: "normalized-base", leftValues: [null, "", "   ", 5, "6"] },
    "left"
  ),
  [null, null, null, 5, 6]
);
const alignedState = buildAdaptiveChartState({
  data: [
    { value: 100, label: "null" },
    { value: 200, label: "blank" },
    { value: 300, label: "space" },
    { value: 400, label: "five" },
    { value: 500, label: "six" },
  ],
  scaleContext: {
    decisionStatus: "pending",
    valueSpace: "normalized-base",
    leftValues: [null, "", "   ", 5, "6"],
    rightValues: [100, 200],
    domain: [0, 200],
  },
  side: "left",
  visualization: "bar-chart",
  selectedScaleMode: "auto",
  drawableHeight: 100,
});
assert.strictEqual(alignedState.canonicalAdaptiveEnabled, true);
assert.deepStrictEqual(alignedState.plotData.map(item => item.label), ["five", "six"]);
assert.deepStrictEqual(alignedState.plotData.map(item => item.value), [5, 6]);

const displayPoint = {
  ...autoState.renderedData[0],
  shortDisplay: "US$ 10m",
};
assert.strictEqual(displayPoint.display, "US$ 10 million");
assert.strictEqual(displayPoint.originalDisplay, "$10,000,000");
assert.strictEqual(
  tooltipLineForParam({ marker: "●", name: "2022", data: displayPoint }),
  "●2022: US$ 10 million"
);
assert.strictEqual(labelValueForParam({ data: displayPoint }), "US$ 10m");
assert.strictEqual(
  labelValueForParam({ data: { display: "US$ 10 million", originalDisplay: "$10,000,000" } }),
  "US$ 10 million"
);

const symlogState = buildAdaptiveChartState({
  data: fieldData,
  scaleContext: {
    decisionStatus: "pending",
    valueSpace: "normalized-base",
    leftValues: [-1, 1],
    rightValues: [-1000, 1000],
    domain: [-1000, 1000],
  },
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "auto",
  drawableHeight: 100,
});
assert.strictEqual(symlogState.resolvedScaleMode, "symlog");
assert.deepStrictEqual(
  symlogState.renderedData.map(item => Number(item.value.toFixed(6))),
  [-0.693147, 0.693147]
);
assert.deepStrictEqual(
  symlogState.renderedData.map(item => item.originalValue),
  [-1, 1]
);
assert.deepStrictEqual(
  symlogState.renderedData.map(item => item.display),
  ["US$ 10 million", "US$ 20 million"]
);

const emptyState = buildAdaptiveChartState({
  data: [],
  scaleContext: positiveContext,
  side: "left",
  visualization: "line-chart",
  selectedScaleMode: "auto",
  drawableHeight: 100,
});
assert.strictEqual(emptyState.decision.mode, "linear");
assert.strictEqual(emptyState.adaptiveTriggered, false);
assert.deepStrictEqual(emptyState.renderedData, []);

function renderSsr(option) {
  const chart = echarts.init(null, null, {
    renderer: "svg",
    ssr: true,
    width: 800,
    height: 480,
  });
  assert.doesNotThrow(() => chart.setOption(option, true));
  chart.dispose();
}

function optionTooltip(option, dataIndex = 0) {
  const data = option.series[0].data[dataIndex];
  return option.tooltip.formatter([{
    marker: "●",
    name: option.xAxis.data[dataIndex],
    data,
    dataIndex,
  }]);
}

function optionLabel(option, dataIndex = 0) {
  return option.series[0].label.formatter({
    data: option.series[0].data[dataIndex],
    dataIndex,
  });
}

const autoLineBuild = buildFullChartLineOption({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  fieldKey: "Output",
  axisType: "number",
});
assert.strictEqual(autoLineBuild.state.resolvedScaleMode, "log");
assert.strictEqual(autoLineBuild.option.yAxis.type, "log");
assert.strictEqual(autoLineBuild.option.tooltip.axisPointer, undefined);
assert.deepStrictEqual(autoLineBuild.option.xAxis.data, ["2022", "2023"]);
assert.deepStrictEqual(
  autoLineBuild.option.series[0].data.map(item => item.originalValue),
  [1, 1.5]
);
assert.strictEqual(optionTooltip(autoLineBuild.option, 0), "●2022: US$ 10 million");
assert.strictEqual(optionLabel(autoLineBuild.option, 0), "US$ 10 million");
renderSsr(autoLineBuild.option);

const forcedLinearLineBuild = buildFullChartLineOption({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  selectedScaleMode: "linear",
  drawableHeight: 100,
  fieldKey: "Output",
  axisType: "number",
});
assert.strictEqual(forcedLinearLineBuild.state.resolvedScaleMode, "linear");
assert.deepStrictEqual(forcedLinearLineBuild.state.rawDomain, positiveContext.domain);
assert.deepStrictEqual(
  [forcedLinearLineBuild.option.yAxis.min, forcedLinearLineBuild.option.yAxis.max],
  positiveContext.domain
);
renderSsr(forcedLinearLineBuild.option);

const indexLineBuild = buildFullChartLineOption({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  selectedScaleMode: "index",
  drawableHeight: 100,
  fieldKey: "Output",
  axisType: "number",
});
assert.strictEqual(indexLineBuild.state.resolvedScaleMode, "index");
assert.deepStrictEqual(indexLineBuild.state.rawDomain, [94, 156]);
assert.notDeepStrictEqual(indexLineBuild.state.rawDomain, positiveContext.domain);
assert.deepStrictEqual(indexLineBuild.option.series[0].data.map(item => item.value), [100, 150]);
renderSsr(indexLineBuild.option);

const symlogLineBuild = buildFullChartLineOption({
  data: fieldData,
  scaleContext: {
    decisionStatus: "pending",
    valueSpace: "normalized-base",
    leftValues: [-1, 1],
    rightValues: [-1000, 1000],
    domain: [-1000, 1000],
  },
  side: "left",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  fieldKey: "Balance",
  axisType: "number",
});
assert.strictEqual(symlogLineBuild.state.resolvedScaleMode, "symlog");
assert.strictEqual(symlogLineBuild.option.yAxis.type, "value");
assert.deepStrictEqual(
  symlogLineBuild.option.series[0].data.map(item => item.originalValue),
  [-1, 1]
);
assert.strictEqual(optionTooltip(symlogLineBuild.option, 1), "●2023: US$ 20 million");
renderSsr(symlogLineBuild.option);

const scatterBarBuild = buildFullChartBarOption({
  data: fieldData,
  scaleContext: positiveContext,
  side: "left",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  fieldKey: "Output",
  axisType: "number",
});
assert.strictEqual(scatterBarBuild.state.resolvedScaleMode, "log");
assert.strictEqual(scatterBarBuild.option.series[0].type, "scatter");
assert.strictEqual(scatterBarBuild.option.tooltip.axisPointer.type, "shadow");
assert.deepStrictEqual(
  scatterBarBuild.option.series[0].data.map(item => item.originalValue),
  [1, 1.5]
);
assert.strictEqual(optionTooltip(scatterBarBuild.option, 0), "●2022: US$ 10 million");
renderSsr(scatterBarBuild.option);

const orderedLineBuild = buildFullChartLineOption({
  data: [
    { value: 20, year: 2023, label: "later", display: "20" },
    { value: 10, year: 2022, label: "earlier", display: "10" },
  ],
  scaleContext: {
    ...positiveContext,
    leftValues: [20, 10],
  },
  side: "left",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  fieldKey: "Series",
  axisType: "number",
});
assert.deepStrictEqual(orderedLineBuild.option.xAxis.data, ["2022", "2023"]);
assert.deepStrictEqual(
  orderedLineBuild.option.series[0].data.map(item => item.originalValue),
  [10, 20]
);
renderSsr(orderedLineBuild.option);

const missingYearLineBuild = buildFullChartLineOption({
  data: missingYearPoints.map(item => ({ ...item, display: String(item.value) })),
  scaleContext: {
    ...positiveContext,
    leftValues: [30, 10, 20],
  },
  side: "left",
  selectedScaleMode: "index",
  drawableHeight: 100,
  fieldKey: "Series",
  axisType: "number",
});
assert.deepStrictEqual(missingYearLineBuild.option.xAxis.data, ["2022", "missing", "2020"]);
assert.deepStrictEqual(
  missingYearLineBuild.state.orderedData.map(item => item.label),
  ["first", "missing", "last"]
);
renderSsr(missingYearLineBuild.option);

const invalidContextBarBuild = buildFullChartBarOption({
  data: fieldData,
  scaleContext: { ...positiveContext, valueSpace: "raw" },
  side: "left",
  selectedScaleMode: "auto",
  drawableHeight: 100,
  fieldKey: "Output",
  axisType: "number",
});
assert.strictEqual(invalidContextBarBuild.state.canonicalAdaptiveEnabled, false);
assert.strictEqual(invalidContextBarBuild.state.resolvedScaleMode, "linear");
assert.deepStrictEqual(invalidContextBarBuild.state.rawDomain, [0, 22]);
assert.strictEqual(invalidContextBarBuild.option.series[0].type, "bar");
renderSsr(invalidContextBarBuild.option);

assert(fullChartSource.includes("buildFullChartBarOption"));
assert(fullChartSource.includes("buildFullChartLineOption"));
assert(/const result = buildFullChartBarOption\(adaptiveOptionArgs\("bar-chart"\)\)/.test(fullChartSource));
assert(/const result = buildFullChartLineOption\(adaptiveOptionArgs\("line-chart"\)\)/.test(fullChartSource));
assert(
  fullChartSource.includes(
    "scaleContext: chartVisualization.value === visualization ? props.scaleContext : null"
  ),
  "pie/stacked fallbacks must stay local-linear instead of entering the adaptive bar path"
);
assert(/chartVisualization\.value === "pie-chart"\) return pieOption\(\)/.test(fullChartSource));
assert(/chartVisualization\.value === "stacked-chart"\) return stackedOption\(\)/.test(fullChartSource));
assert(!fullChartSource.includes("const axisForScale ="));

assert(fullChartSource.includes('class="scale-mode-switch"'));
assert(fullChartSource.includes("dataLength: numericData.value.length"));
assert(fullChartSource.includes("orderedLinePoints"));
assert(/const resize = \(\) => scheduleRenderChart\(\);/.test(fullChartSource));
assert(fullChartSource.includes("scheduleRenderChart"));
assert(fullChartSource.includes("cancelScheduledRender"));
assert(fullChartSource.includes("requestAnimationFrame"));
assert(fullChartSource.includes("cancelAnimationFrame"));
assert(fullChartSource.includes("scaleDecision.value = linearScaleDecision();"));
assert(!fullChartSource.includes("nextTick(renderChart);"));

console.log("fullChartAdaptiveScale executable tests passed");
