const assert = require("assert");
const {
  MIN_VISIBLE_BAR_PX,
  MIN_VISIBLE_TREND_PX,
  SYMLOG_CONSTANT,
  PREVIEW_DRAWABLE_HEIGHT,
  adaptiveDomain,
  detectAdaptiveScale,
  scaleValue,
  trendChange,
  trendIndexPoints,
  unscaleValue,
} = require("../src/js/adaptiveChartScale");

assert.strictEqual(MIN_VISIBLE_BAR_PX, 3);
assert.strictEqual(MIN_VISIBLE_TREND_PX, 4);
assert.strictEqual(SYMLOG_CONSTANT, 1);
assert.strictEqual(PREVIEW_DRAWABLE_HEIGHT, 58);

const visibleDespiteLargeRatio = detectAdaptiveScale({
  leftValues: [5],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 84,
  visualization: "bar-chart",
});
assert.strictEqual(visibleDespiteLargeRatio.mode, "linear");
assert.strictEqual(visibleDespiteLargeRatio.reason, null);

for (const missingEndpoint of [null, undefined, "", "   "]) {
  const invalidStartDomain = detectAdaptiveScale({
    leftValues: [1],
    rightValues: [100],
    domain: [missingEndpoint, 100],
    drawableHeight: 100,
    visualization: "bar-chart",
  });
  assert.strictEqual(invalidStartDomain.mode, "linear");
  assert.strictEqual(invalidStartDomain.reason, null);
  assert.strictEqual(invalidStartDomain.diagnostics.leftMinPixels, null);

  const invalidEndDomain = detectAdaptiveScale({
    leftValues: [-1],
    rightValues: [-100],
    domain: [-100, missingEndpoint],
    drawableHeight: 100,
    visualization: "bar-chart",
  });
  assert.strictEqual(invalidEndDomain.mode, "linear");
  assert.strictEqual(invalidEndDomain.reason, null);
  assert.strictEqual(invalidEndDomain.diagnostics.rightMinPixels, null);
}

const hiddenPositiveBar = detectAdaptiveScale({
  leftValues: [1],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 84,
  visualization: "bar-chart",
});
assert.strictEqual(hiddenPositiveBar.mode, "log");
assert.strictEqual(hiddenPositiveBar.constrainedSide, "left");
assert.strictEqual(hiddenPositiveBar.reason, "bar-below-visible-threshold");
assert(hiddenPositiveBar.diagnostics.leftMinPixels < MIN_VISIBLE_BAR_PX);

const zeroIsNotHiddenData = detectAdaptiveScale({
  leftValues: [0],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 84,
  visualization: "bar-chart",
});
assert.strictEqual(zeroIsNotHiddenData.mode, "linear");

const signedHiddenBar = detectAdaptiveScale({
  leftValues: [-1],
  rightValues: [1000],
  domain: [-1, 1000],
  drawableHeight: 84,
  visualization: "bar-chart",
});
assert.strictEqual(signedHiddenBar.mode, "symlog");
assert.strictEqual(signedHiddenBar.constrainedSide, "left");

const flatLineIsDataFact = detectAdaptiveScale({
  leftValues: [5, 5, 5],
  rightValues: [10, 500, 1000],
  domain: [0, 1000],
  drawableHeight: 58,
  visualization: "line-chart",
});
assert.strictEqual(flatLineIsDataFact.mode, "linear");

const compressedTrend = detectAdaptiveScale({
  leftValues: [1, 2, 3],
  rightValues: [10, 500, 1000],
  domain: [0, 1000],
  drawableHeight: 58,
  visualization: "line-chart",
});
assert.strictEqual(compressedTrend.mode, "log");
assert.strictEqual(compressedTrend.reason, "trend-below-visible-threshold");
assert(compressedTrend.diagnostics.leftTrendPixels < MIN_VISIBLE_TREND_PX);

const bothVisible = detectAdaptiveScale({
  leftValues: [10, 40],
  rightValues: [60, 100],
  domain: [0, 100],
  drawableHeight: 58,
  visualization: "line-chart",
});
assert.strictEqual(bothVisible.mode, "linear");

const invalidAndSinglePoint = detectAdaptiveScale({
  leftValues: [NaN, Infinity, 2],
  rightValues: [null, undefined, 3],
  domain: [0, 3],
  drawableHeight: 58,
  visualization: "line-chart",
});
assert.strictEqual(invalidAndSinglePoint.mode, "linear");

const smallTrendVsFlatLine = detectAdaptiveScale({
  leftValues: [1, 2, 3],
  rightValues: [100, 100, 100],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "line-chart",
});
assert.strictEqual(smallTrendVsFlatLine.mode, "linear");
assert.strictEqual(smallTrendVsFlatLine.diagnostics.rightTrendPixels, null);

const smallTrendVsSinglePoint = detectAdaptiveScale({
  leftValues: [1, 2, 3],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "line-chart",
});
assert.strictEqual(smallTrendVsSinglePoint.mode, "linear");

const smallTrendVsInvalidData = detectAdaptiveScale({
  leftValues: [1, 2, 3],
  rightValues: [null, undefined, "", NaN, Infinity],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "line-chart",
});
assert.strictEqual(smallTrendVsInvalidData.mode, "linear");

const dominantVisibleBarControlsCategoryDecision = detectAdaptiveScale({
  leftValues: [1, 20, 50],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "bar-chart",
});
assert.strictEqual(dominantVisibleBarControlsCategoryDecision.mode, "linear");
assert.strictEqual(dominantVisibleBarControlsCategoryDecision.diagnostics.leftMinPixels, 50);

const dominantHiddenBarControlsCategoryDecision = detectAdaptiveScale({
  leftValues: [0, 1, 2],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "bar-chart",
});
assert.strictEqual(dominantHiddenBarControlsCategoryDecision.mode, "symlog");
assert.strictEqual(dominantHiddenBarControlsCategoryDecision.constrainedSide, "left");
assert.strictEqual(dominantHiddenBarControlsCategoryDecision.diagnostics.leftMinPixels, 2);

const exactBarThreshold = detectAdaptiveScale({
  leftValues: [3],
  rightValues: [100],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "bar-chart",
});
assert.strictEqual(exactBarThreshold.diagnostics.leftMinPixels, MIN_VISIBLE_BAR_PX);
assert.strictEqual(exactBarThreshold.mode, "linear");

const exactTrendThreshold = detectAdaptiveScale({
  leftValues: [0, 4],
  rightValues: [0, 100],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "line-chart",
});
assert.strictEqual(exactTrendThreshold.diagnostics.leftTrendPixels, MIN_VISIBLE_TREND_PX);
assert.strictEqual(exactTrendThreshold.mode, "linear");

const rightConstrainedBar = detectAdaptiveScale({
  leftValues: [100],
  rightValues: [1],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "bar-chart",
});
assert.strictEqual(rightConstrainedBar.mode, "log");
assert.strictEqual(rightConstrainedBar.constrainedSide, "right");

const rightConstrainedTrendWithZero = detectAdaptiveScale({
  leftValues: [0, 100],
  rightValues: [1, 3],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "line-chart",
});
assert.strictEqual(rightConstrainedTrendWithZero.mode, "symlog");
assert.strictEqual(rightConstrainedTrendWithZero.constrainedSide, "right");

const bothTrendsBelowThreshold = detectAdaptiveScale({
  leftValues: [1, 2],
  rightValues: [3, 4],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "line-chart",
});
assert.strictEqual(bothTrendsBelowThreshold.mode, "linear");

const bothBarsBelowThreshold = detectAdaptiveScale({
  leftValues: [1],
  rightValues: [2],
  domain: [0, 100],
  drawableHeight: 100,
  visualization: "bar-chart",
});
assert.strictEqual(bothBarsBelowThreshold.mode, "linear");

const sortedChange = trendChange([
  { year: 2024, value: 150 },
  { year: 2020, value: 100 },
  { year: 2022, value: 120 },
]);
assert.deepStrictEqual(sortedChange, {
  firstValue: 100,
  lastValue: 150,
  absoluteChange: 50,
  percentChange: 50,
  firstYear: 2020,
  lastYear: 2024,
});

const zeroStartChange = trendChange([
  { year: 2020, value: 0 },
  { year: 2024, value: 10 },
]);
assert.strictEqual(zeroStartChange.absoluteChange, 10);
assert.strictEqual(zeroStartChange.percentChange, null);

const invalidValuesAreFiltered = trendChange([
  { year: 2019, value: null },
  { year: 2020, value: undefined },
  { year: 2021, value: "" },
  { year: 2022, value: "10" },
  { year: 2023, value: 20 },
]);
assert.deepStrictEqual(invalidValuesAreFiltered, {
  firstValue: 10,
  lastValue: 20,
  absoluteChange: 10,
  percentChange: 100,
  firstYear: 2022,
  lastYear: 2023,
});

assert.deepStrictEqual(
  trendIndexPoints([
    { year: 2019, value: null },
    { year: 2020, value: "" },
    { year: 2021, value: 10 },
    { year: 2022, value: 20 },
  ]).map(point => ({ year: point.year, value: point.value, originalValue: point.originalValue })),
  [
    { year: 2021, value: 100, originalValue: 10 },
    { year: 2022, value: 200, originalValue: 20 },
  ]
);

const missingYearKeepsInputOrder = trendChange([
  { year: 2024, value: 150 },
  { year: null, value: 100 },
  { year: 2020, value: 120 },
]);
assert.deepStrictEqual(missingYearKeepsInputOrder, {
  firstValue: 150,
  lastValue: 120,
  absoluteChange: -30,
  percentChange: -20,
  firstYear: 2024,
  lastYear: 2020,
});

for (const missingYear of [null, undefined, ""]) {
  const changeWithMissingFirstYear = trendChange([
    { year: missingYear, value: 100 },
    { year: 2024, value: 150 },
  ]);
  assert.strictEqual(changeWithMissingFirstYear.firstYear, null);
  assert.strictEqual(changeWithMissingFirstYear.lastYear, 2024);

  const changeWithMissingLastYear = trendChange([
    { year: 2020, value: 100 },
    { year: missingYear, value: 150 },
  ]);
  assert.strictEqual(changeWithMissingLastYear.firstYear, 2020);
  assert.strictEqual(changeWithMissingLastYear.lastYear, null);
}

assert.deepStrictEqual(
  trendIndexPoints([
    { year: 2024, value: 100 },
    { year: null, value: 200 },
    { year: 2020, value: 300 },
  ]).map(point => point.originalValue),
  [100, 200, 300]
);

assert.deepStrictEqual(
  trendIndexPoints([
    { year: 2024, value: 150, display: "150" },
    { year: 2020, value: 100, display: "100" },
  ]).map(point => ({ year: point.year, value: point.value, originalValue: point.originalValue })),
  [
    { year: 2020, value: 100, originalValue: 100 },
    { year: 2024, value: 150, originalValue: 150 },
  ]
);
assert.deepStrictEqual(
  trendIndexPoints([{ year: 2020, value: 0 }, { year: 2024, value: 10 }]),
  []
);

assert.deepStrictEqual(
  adaptiveDomain([-10000, 10000], "linear", [100, -100]),
  [-100, 100]
);
assert.deepStrictEqual(
  adaptiveDomain([999], "linear", ["10", "-10"]),
  [-10, 10]
);

const logDomain = adaptiveDomain([1, 1000], "log", [0, 1000]);
assert(logDomain[0] > 0);
assert(logDomain[0] < 1);
assert(logDomain[1] > 1000);

for (const extremeValues of [
  [Number.MAX_VALUE],
  [Number.MAX_VALUE / 2, Number.MAX_VALUE],
  [Number.MIN_VALUE],
  [Number.MIN_VALUE, Number.MAX_VALUE],
]) {
  const extremeLogDomain = adaptiveDomain(extremeValues, "log", [1, Number.MAX_VALUE]);
  assert(Number.isFinite(extremeLogDomain[0]));
  assert(Number.isFinite(extremeLogDomain[1]));
  assert(extremeLogDomain[0] > 0);
  assert(extremeLogDomain[0] < extremeLogDomain[1]);
  assert(extremeLogDomain[0] <= Math.min(...extremeValues));
  assert(extremeLogDomain[1] >= Math.max(...extremeValues));
}

assert.deepStrictEqual(
  adaptiveDomain([-1000, 0, 1000], "symlog", [-10, 10]),
  [-1000, 1000]
);

for (const mode of ["linear", "log"]) {
  for (const value of [-1000, -1, 0, 1, 1000]) {
    assert.strictEqual(scaleValue(value, mode), value);
    assert.strictEqual(unscaleValue(value, mode), value);
  }
}

for (const mode of ["linear", "log", "symlog"]) {
  for (const missingValue of [null, undefined, ""]) {
    assert.strictEqual(scaleValue(missingValue, mode), null);
    assert.strictEqual(unscaleValue(missingValue, mode), null);
  }
}

for (const value of [-1000, -1, 0, 1, 1000]) {
  const transformed = scaleValue(value, "symlog");
  const restored = unscaleValue(transformed, "symlog");
  assert(Math.abs(restored - value) < 1e-9);
}

console.log("adaptiveChartScale tests passed");
