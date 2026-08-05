const assert = require("assert");
const fs = require("fs");
const path = require("path");
const echarts = require("echarts");

const { detectAdaptiveScale, scaleValue } = require("../src/js/adaptiveChartScale");
const { barChartDomain } = require("../src/js/chartValueDisplay");
const { PAPER_PIE_COLORS } = require("../src/js/chartTheme");
const { buildMergedComparison } = require("../src/js/mergedComparisonData");
const {
  buildMergedAdaptiveState,
  buildMergedComparisonOption,
  linearScaleDecision,
} = require("../src/js/mergedComparisonAdaptiveOptions");

const source = fs.readFileSync(
  path.join(__dirname, "..", "src", "components", "compoents_base", "MergedComparisonChart.vue"),
  "utf8"
);

function point(value, year, display = String(value)) {
  return { value, year, label: String(year), display, raw: display };
}

const positiveLine = {
  mode: "line",
  yDomain: [0, 2200],
  categories: ["2022", "2023"],
  series: [
    { name: "Left", data: [point(1, 2022, "1"), point(2, 2023, "2")] },
    { name: "Right", data: [point(1000, 2022, "1,000"), point(2000, 2023, "2,000")] },
  ],
  scaleContext: {
    leftValues: [1, 2],
    rightValues: [1000, 2000],
    domain: [0, 2200],
    visualization: "line-chart",
  },
};

const shortDecision = detectAdaptiveScale({
  ...positiveLine.scaleContext,
  drawableHeight: 302,
});
assert.strictEqual(shortDecision.mode, "log");
const tallDecision = detectAdaptiveScale({
  ...positiveLine.scaleContext,
  drawableHeight: 10000,
});
assert.strictEqual(tallDecision.mode, "linear");

const autoState = buildMergedAdaptiveState({
  data: positiveLine,
  selectedScaleMode: "auto",
  scaleDecision: shortDecision,
});
assert.strictEqual(autoState.adaptiveTriggered, true);
assert.strictEqual(autoState.resolvedScaleMode, "log");
assert.strictEqual(autoState.seriesType, "line");
assert(autoState.rawDomain[0] > 0, "native log domain must contain only positive values");
assert.deepStrictEqual(
  autoState.renderedSeries.map(series => series.data.map(item => item.originalValue)),
  [[1, 2], [1000, 2000]]
);
assert.deepStrictEqual(
  autoState.renderedSeries.map(series => series.data.map(item => item.display)),
  [["1", "2"], ["1,000", "2,000"]]
);

const linearState = buildMergedAdaptiveState({
  data: positiveLine,
  selectedScaleMode: "linear",
  scaleDecision: shortDecision,
});
assert.strictEqual(linearState.resolvedScaleMode, "linear");
assert.deepStrictEqual(linearState.rawDomain, positiveLine.scaleContext.domain);

const missingYearLine = {
  mode: "line",
  yDomain: [0, 11000],
  categories: ["2020", "2021", "2022"],
  series: [
    {
      name: "Left",
      data: [point(10, 2020, "10"), { value: null, display: "-", label: "2021" }, point(20, 2022, "20")],
    },
    {
      name: "Right",
      data: [point(10000, 2020, "10,000"), point(5000, 2021, "5,000"), point(2500, 2022, "2,500")],
    },
  ],
  scaleContext: {
    leftValues: [10, 20],
    rightValues: [10000, 5000, 2500],
    domain: [0, 11000],
    visualization: "line-chart",
  },
};
const indexDecision = detectAdaptiveScale({
  ...missingYearLine.scaleContext,
  drawableHeight: 302,
});
assert.strictEqual(indexDecision.mode, "log");
const indexState = buildMergedAdaptiveState({
  data: missingYearLine,
  selectedScaleMode: "index",
  scaleDecision: indexDecision,
});
assert.strictEqual(indexState.canUseTrendIndex, true);
assert.strictEqual(indexState.resolvedScaleMode, "index");
assert.deepStrictEqual(
  indexState.renderedSeries[0].data.map(item => item.value),
  [100, null, 200],
  "missing categories must remain aligned after per-side indexing"
);
assert.deepStrictEqual(
  indexState.renderedSeries[1].data.map(item => item.value),
  [100, 50, 25]
);
assert.deepStrictEqual(indexState.rawDomain, [4, 221]);
assert.notDeepStrictEqual(indexState.rawDomain, missingYearLine.scaleContext.domain);
assert.strictEqual(indexState.renderedSeries[0].data[2].originalValue, 20);
assert.strictEqual(indexState.renderedSeries[0].data[2].display, "20");

const singlePositive = {
  mode: "single",
  yDomain: [0, 1100],
  categories: ["Value"],
  series: [
    { name: "Left", data: [{ value: 1, display: "1", raw: "1" }] },
    { name: "Right", data: [{ value: 1000, display: "1,000", raw: "1,000" }] },
  ],
  scaleContext: {
    leftValues: [1],
    rightValues: [1000],
    domain: [0, 1100],
    visualization: "bar-chart",
  },
};
const singleDecision = detectAdaptiveScale({
  ...singlePositive.scaleContext,
  drawableHeight: 302,
});
const singleState = buildMergedAdaptiveState({
  data: singlePositive,
  selectedScaleMode: "auto",
  scaleDecision: singleDecision,
});
assert.strictEqual(singleState.compressedSingle, true);
assert.strictEqual(singleState.seriesType, "scatter");

const categoricalBar = {
  ...positiveLine,
  mode: "bar",
  scaleContext: { ...positiveLine.scaleContext, visualization: "bar-chart" },
};
const categoricalDecision = detectAdaptiveScale({
  ...categoricalBar.scaleContext,
  drawableHeight: 302,
});
assert.strictEqual(categoricalDecision.mode, "log");
const categoricalState = buildMergedAdaptiveState({
  data: categoricalBar,
  selectedScaleMode: "auto",
  scaleDecision: categoricalDecision,
});
assert.strictEqual(categoricalState.compressedSingle, false);
assert.strictEqual(categoricalState.compressedBar, true);
assert.strictEqual(categoricalState.seriesType, "scatter");

const signedSingle = {
  ...singlePositive,
  yDomain: [-1100, 1100],
  series: [
    { name: "Left", data: [{ value: -1, display: "-1", raw: "-1" }] },
    { name: "Right", data: [{ value: -1000, display: "-1,000", raw: "-1,000" }] },
  ],
  scaleContext: {
    leftValues: [-1],
    rightValues: [-1000],
    domain: [-1100, 1100],
    visualization: "bar-chart",
  },
};
const symlogDecision = detectAdaptiveScale({
  ...signedSingle.scaleContext,
  drawableHeight: 302,
});
assert.strictEqual(symlogDecision.mode, "symlog");
const symlogState = buildMergedAdaptiveState({
  data: signedSingle,
  selectedScaleMode: "auto",
  scaleDecision: symlogDecision,
});
assert.strictEqual(symlogState.resolvedScaleMode, "symlog");
assert.strictEqual(symlogState.renderedSeries[0].data[0].value, scaleValue(-1, "symlog"));
assert.strictEqual(symlogState.renderedSeries[0].data[0].originalValue, -1);
assert.strictEqual(symlogState.renderedSeries[0].data[0].display, "-1");

const invalidState = buildMergedAdaptiveState({
  data: { ...positiveLine, scaleContext: { ...positiveLine.scaleContext, domain: null } },
  selectedScaleMode: "auto",
  scaleDecision: shortDecision,
});
assert.strictEqual(invalidState.validScaleContext, false);
assert.strictEqual(invalidState.adaptiveTriggered, false);
assert.strictEqual(invalidState.resolvedScaleMode, "linear");

const stackedState = buildMergedAdaptiveState({
  data: {
    ...singlePositive,
    mode: "stacked",
    scaleContext: { ...singlePositive.scaleContext, visualization: "stacked-chart" },
  },
  selectedScaleMode: "auto",
  scaleDecision: shortDecision,
});
assert.strictEqual(stackedState.adaptiveTriggered, false);
assert.strictEqual(stackedState.resolvedScaleMode, "linear");
assert.deepStrictEqual(stackedState.rawDomain, [0, 100]);
assert.strictEqual(stackedState.seriesType, "bar");

const pieOriginState = buildMergedAdaptiveState({
  data: {
    ...singlePositive,
    mode: "bar",
    scaleContext: { ...singlePositive.scaleContext, adaptiveEligible: false },
  },
  selectedScaleMode: "auto",
  scaleDecision: singleDecision,
});
assert.strictEqual(pieOriginState.validScaleContext, false);
assert.strictEqual(pieOriginState.adaptiveTriggered, false);
assert.strictEqual(pieOriginState.resolvedScaleMode, "linear");
assert.strictEqual(pieOriginState.seriesType, "bar");

const noDecisionState = buildMergedAdaptiveState({ data: positiveLine });
assert.deepStrictEqual(noDecisionState.scaleDecision, linearScaleDecision());

function tooltipHtml(option, seriesIndex = 0, dataIndex = 0) {
  const series = option.series[seriesIndex];
  const data = series.data[dataIndex];
  return option.tooltip.formatter([{
    marker: "●",
    seriesName: series.name,
    name: option.xAxis.data[dataIndex],
    data,
  }]);
}

function labelText(option, seriesIndex = 0, dataIndex = 0) {
  return option.series[seriesIndex].label.formatter({
    data: option.series[seriesIndex].data[dataIndex],
  });
}

const grid = { top: 48, left: 56, right: 28, bottom: 42, containLabel: true };
const autoOption = buildMergedComparisonOption({ data: positiveLine, state: autoState, grid });
assert.strictEqual(autoOption.yAxis.type, "log");
assert.deepStrictEqual(
  [autoOption.yAxis.min, autoOption.yAxis.max],
  autoState.transformedDomain
);
assert.strictEqual(autoOption.yAxis.axisLabel.formatter(1000), "1K");
assert.strictEqual(tooltipHtml(autoOption, 1, 0), "●Right: 1,000");
assert.strictEqual(labelText(autoOption, 1, 0), "1,000");

function assertPlainLetterCategory(unitLabel) {
  const data = buildMergedComparison({
    label: "Ratings",
    dataType: "Numerical",
    mergeVisualization: "bar-chart",
    visualization: {
      left: {
        raw: `A 10 ${unitLabel} 20`,
        values: [
          { value: 10, label: "A" },
          { value: 20, label: unitLabel },
        ],
      },
      right: {
        raw: `A 30 ${unitLabel} 40`,
        values: [
          { value: 30, label: "A" },
          { value: 40, label: unitLabel },
        ],
      },
    },
  }, { left: "Left", right: "Right" });
  assert.strictEqual(data.mode, "bar");
  assert.deepStrictEqual(data.categories, ["A", unitLabel]);
  assert.deepStrictEqual(
    data.series.map(series => series.data.map(point => point.value)),
    [[10, 20], [30, 40]]
  );
  assert.deepStrictEqual(
    data.series.map(series => series.data.map(point => point.display)),
    [["10", "20"], ["30", "40"]]
  );
  assert.deepStrictEqual(data.scaleContext.domain, barChartDomain([10, 20, 30, 40]));
  const decision = detectAdaptiveScale({
    ...data.scaleContext,
    drawableHeight: 302,
  });
  assert.strictEqual(decision.mode, "linear");
  const state = buildMergedAdaptiveState({
    data,
    selectedScaleMode: "auto",
    scaleDecision: decision,
  });
  assert.deepStrictEqual(
    state.renderedSeries.map(series => series.data.map(point => point.originalValue)),
    [[10, 20], [30, 40]]
  );
  const option = buildMergedComparisonOption({ data, state, grid });
  assert.strictEqual(labelText(option, 0, 0), "10");
  assert.strictEqual(labelText(option, 0, 1), "20");
  const chart = echarts.init(null, null, {
    renderer: "svg",
    ssr: true,
    width: 800,
    height: 480,
  });
  assert.doesNotThrow(() => chart.setOption(option, true));
  chart.dispose();
}

assertPlainLetterCategory("B");
for (const category of ["M", "T", "K"]) assertPlainLetterCategory(category);

const canonicalMagnitudeData = buildMergedComparison({
  label: "Economic output",
  dataType: "Numerical",
  mergeVisualization: "bar-chart",
  visualization: {
    left: {
      raw: "$1.87 trillion",
      values: [{ value: 1.87, raw: "$1.87 trillion" }],
    },
    right: {
      raw: "$814.9 billion",
      values: [{ value: 814.9, raw: "$814.9 billion" }],
    },
  },
}, { left: "Left", right: "Right" });
assert.strictEqual(canonicalMagnitudeData.mode, "bar");
assert.deepStrictEqual(
  canonicalMagnitudeData.series.map(series => series.data[0].value),
  [1870000000000, 814900000000]
);
assert.deepStrictEqual(
  canonicalMagnitudeData.series.map(series => series.data[0].display),
  ["$1.87 trillion", "$814.9 billion"]
);
assert.deepStrictEqual(canonicalMagnitudeData.scaleContext.leftValues, [1870000000000]);
assert.deepStrictEqual(canonicalMagnitudeData.scaleContext.rightValues, [814900000000]);
assert.deepStrictEqual(
  canonicalMagnitudeData.scaleContext.domain,
  barChartDomain([1870000000000, 814900000000])
);
const canonicalMagnitudeDecision = detectAdaptiveScale({
  ...canonicalMagnitudeData.scaleContext,
  drawableHeight: 302,
});
assert.strictEqual(canonicalMagnitudeDecision.mode, "linear");
const canonicalMagnitudeState = buildMergedAdaptiveState({
  data: canonicalMagnitudeData,
  selectedScaleMode: "auto",
  scaleDecision: canonicalMagnitudeDecision,
});
assert.strictEqual(canonicalMagnitudeState.resolvedScaleMode, "linear");
assert.deepStrictEqual(
  canonicalMagnitudeState.renderedSeries.map(series => series.data[0].originalValue),
  [1870000000000, 814900000000]
);
const canonicalMagnitudeOption = buildMergedComparisonOption({
  data: canonicalMagnitudeData,
  state: canonicalMagnitudeState,
  grid,
});
assert.strictEqual(labelText(canonicalMagnitudeOption, 0, 0), "$1.87 trillion");
assert.strictEqual(labelText(canonicalMagnitudeOption, 1, 0), "$814.9 billion");
assert.strictEqual(tooltipHtml(canonicalMagnitudeOption, 0, 0), "●Left: $1.87 trillion");
const canonicalMagnitudeChart = echarts.init(null, null, {
  renderer: "svg",
  ssr: true,
  width: 800,
  height: 480,
});
assert.doesNotThrow(() => canonicalMagnitudeChart.setOption(canonicalMagnitudeOption, true));
canonicalMagnitudeChart.dispose();

const spendingData = buildMergedComparison({
  label: "Spending",
  dataType: "Numerical",
  visualization: {
    left: {
      raw: "$456.5 billion (2020)",
      values: [{ value: 456500000000, year: 2020 }],
    },
    right: {
      raw: "¥239,694 billion 43.4% of GDP (2022)",
      values: [{ value: 239694000000000, year: 2022 }],
    },
  },
}, { left: "South Korea", right: "Japan" });
const spendingDecision = detectAdaptiveScale({
  ...spendingData.scaleContext,
  drawableHeight: 302,
});
const spendingState = buildMergedAdaptiveState({
  data: spendingData,
  selectedScaleMode: "auto",
  scaleDecision: spendingDecision,
});
const spendingOption = buildMergedComparisonOption({
  data: spendingData,
  state: spendingState,
  grid,
});
assert.strictEqual(spendingData.series[1].data[1].value, 239694000000000);
assert.deepStrictEqual(spendingData.scaleContext.rightValues, [239694000000000]);
assert.deepStrictEqual(spendingData.scaleContext.domain, [0, 263663400000000.03]);
assert.strictEqual(spendingState.renderedSeries[1].data[1].originalValue, 239694000000000);
assert.strictEqual(labelText(spendingOption, 1, 1), "¥239,694 billion");
assert.strictEqual(tooltipHtml(spendingOption, 1, 1), "●Japan: ¥239,694 billion");

const symlogOption = buildMergedComparisonOption({
  data: signedSingle,
  state: symlogState,
  grid,
});
assert.deepStrictEqual(
  [symlogOption.yAxis.min, symlogOption.yAxis.max],
  symlogState.transformedDomain,
  "the option must consume the state's transformed domain without recomputing it"
);
assert.strictEqual(symlogOption.series[0].data[0].value, scaleValue(-1, "symlog"));
assert.strictEqual(
  symlogOption.yAxis.axisLabel.formatter(scaleValue(-1000, "symlog")),
  "-1K"
);
assert.strictEqual(tooltipHtml(symlogOption, 0, 0), "●Left: -1");
assert.strictEqual(labelText(symlogOption, 0, 0), "-1");

const indexOption = buildMergedComparisonOption({
  data: missingYearLine,
  state: indexState,
  grid,
});
assert.deepStrictEqual(
  [indexOption.yAxis.min, indexOption.yAxis.max],
  indexState.transformedDomain
);
assert.notDeepStrictEqual(
  [indexOption.yAxis.min, indexOption.yAxis.max],
  missingYearLine.scaleContext.domain
);
assert.deepStrictEqual(indexOption.series[0].data.map(item => item.value), [100, null, 200]);
assert.strictEqual(indexOption.yAxis.name, "趋势指数（首值=100）");
assert.strictEqual(tooltipHtml(indexOption, 0, 2), "●Left: 20");
assert.strictEqual(labelText(indexOption, 0, 2), "20");

const singleOption = buildMergedComparisonOption({
  data: singlePositive,
  state: singleState,
  grid,
});
assert(singleOption.series.every(series => series.type === "scatter"));
assert.deepStrictEqual(singleOption.xAxis.data, singlePositive.categories);
assert(singleOption.series.every(series => series.data.length === singlePositive.categories.length));
assert.strictEqual(singleOption.tooltip.axisPointer.type, "line");

const categoricalOption = buildMergedComparisonOption({
  data: categoricalBar,
  state: categoricalState,
  grid,
});
assert(categoricalOption.series.every(series => series.type === "scatter"));
assert.deepStrictEqual(categoricalOption.xAxis.data, categoricalBar.categories);
assert(categoricalOption.series.every(series => series.data.length === categoricalBar.categories.length));
assert.strictEqual(categoricalOption.tooltip.axisPointer.type, "line");

const stackedOption = buildMergedComparisonOption({
  data: {
    ...singlePositive,
    mode: "stacked",
    categories: ["China", "Other"],
    categoryColors: { China: PAPER_PIE_COLORS[0], Other: PAPER_PIE_COLORS[1] },
    series: [
      { name: "Left", data: [{ value: 25, display: "25", raw: "25" }, { value: 75, display: "75", raw: "75" }] },
      { name: "Right", data: [{ value: 30, display: "30", raw: "30" }, { value: 70, display: "70", raw: "70" }] },
    ],
  },
  state: stackedState,
  grid,
});
assert.deepStrictEqual([stackedOption.yAxis.min, stackedOption.yAxis.max], [0, 100]);
assert(stackedOption.series.every(series => series.type === "bar"));
assert.deepStrictEqual(stackedOption.xAxis.data, ["Left", "Right"]);
assert.strictEqual(stackedOption.series[0].name, "China");
assert.strictEqual(stackedOption.series[0].itemStyle.color, PAPER_PIE_COLORS[0]);
assert.strictEqual(stackedOption.series[1].itemStyle.color, PAPER_PIE_COLORS[1]);
assert.strictEqual(stackedOption.series[0].data[0].display, "25");

for (const option of [autoOption, spendingOption, symlogOption, indexOption, singleOption, categoricalOption, stackedOption]) {
  const chart = echarts.init(null, null, {
    renderer: "svg",
    ssr: true,
    width: 800,
    height: 480,
  });
  assert.doesNotThrow(() => chart.setOption(option, true));
  chart.dispose();
}

assert(
  /buildMergedComparisonOption/.test(source),
  "the component must call the same executable option builder covered above"
);
assert(
  /createChartRenderController/.test(source),
  "the component must use the executable render controller covered by scheduler tests"
);
assert(!source.includes("PREVIEW_DRAWABLE_HEIGHT"));

console.log("mergedComparisonAdaptiveScale executable tests passed");
