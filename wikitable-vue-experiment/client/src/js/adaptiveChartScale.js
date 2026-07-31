const MIN_VISIBLE_BAR_PX = 3;
const MIN_VISIBLE_TREND_PX = 4;
const SYMLOG_CONSTANT = 1;
const PREVIEW_DRAWABLE_HEIGHT = 58;
const LOG_PADDING_FACTOR = 1.2;

function optionalFiniteNumber(value) {
  if (value === null || value === undefined || (typeof value === "string" && value.trim() === "")) {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function finiteNumbers(values = []) {
  return (Array.isArray(values) ? values : [])
    .map(optionalFiniteNumber)
    .filter(value => value !== null);
}

function validDomain(domain) {
  if (!Array.isArray(domain) || domain.length !== 2) return null;
  const start = optionalFiniteNumber(domain[0]);
  const end = optionalFiniteNumber(domain[1]);
  if (start === null || end === null || start === end) return null;
  return start < end ? [start, end] : [end, start];
}

function projectedY(value, domain, drawableHeight) {
  const safeDomain = validDomain(domain);
  const height = Math.max(0, Number(drawableHeight) || 0);
  if (!safeDomain || height === 0 || !Number.isFinite(Number(value))) return null;
  const [min, max] = safeDomain;
  return height - ((Number(value) - min) / (max - min)) * height;
}

// Category previews use the dominant (largest projected) non-zero bar on each side.
function dominantNonZeroBarPixels(values, domain, drawableHeight) {
  const zeroY = projectedY(0, domain, drawableHeight);
  if (zeroY === null) return null;
  const pixels = finiteNumbers(values)
    .filter(value => value !== 0)
    .map(value => projectedY(value, domain, drawableHeight))
    .filter(Number.isFinite)
    .map(valueY => Math.abs(valueY - zeroY));
  return pixels.length ? Math.max(...pixels) : null;
}

function trendPixels(values, domain, drawableHeight) {
  const numbers = finiteNumbers(values);
  if (numbers.length < 2 || new Set(numbers).size < 2) return null;
  const minY = projectedY(Math.min(...numbers), domain, drawableHeight);
  const maxY = projectedY(Math.max(...numbers), domain, drawableHeight);
  if (!Number.isFinite(minY) || !Number.isFinite(maxY)) return null;
  return Math.abs(maxY - minY);
}

function compressedMode(leftValues, rightValues) {
  const values = [...finiteNumbers(leftValues), ...finiteNumbers(rightValues)];
  return values.length && values.every(value => value > 0) ? "log" : "symlog";
}

function linearDecision(drawableHeight, diagnostics = {}) {
  return {
    mode: "linear",
    constrainedSide: null,
    reason: null,
    diagnostics: {
      drawableHeight: Math.max(0, Number(drawableHeight) || 0),
      leftMinPixels: null,
      rightMinPixels: null,
      leftTrendPixels: null,
      rightTrendPixels: null,
      ...diagnostics,
    },
  };
}

function detectAdaptiveScale({
  leftValues = [],
  rightValues = [],
  domain,
  drawableHeight,
  visualization,
} = {}) {
  const height = Math.max(0, Number(drawableHeight) || 0);
  if (!validDomain(domain) || height === 0) return linearDecision(height);

  if (visualization === "bar-chart") {
    const leftMinPixels = dominantNonZeroBarPixels(leftValues, domain, height);
    const rightMinPixels = dominantNonZeroBarPixels(rightValues, domain, height);
    const diagnostics = {
      leftMinPixels,
      rightMinPixels,
      leftTrendPixels: null,
      rightTrendPixels: null,
    };
    const leftHidden =
      leftMinPixels !== null &&
      leftMinPixels < MIN_VISIBLE_BAR_PX &&
      rightMinPixels !== null &&
      rightMinPixels >= MIN_VISIBLE_BAR_PX;
    const rightHidden =
      rightMinPixels !== null &&
      rightMinPixels < MIN_VISIBLE_BAR_PX &&
      leftMinPixels !== null &&
      leftMinPixels >= MIN_VISIBLE_BAR_PX;
    if (!leftHidden && !rightHidden) return linearDecision(height, diagnostics);
    return {
      mode: compressedMode(leftValues, rightValues),
      constrainedSide: leftHidden ? "left" : "right",
      reason: "bar-below-visible-threshold",
      diagnostics: { drawableHeight: height, ...diagnostics },
    };
  }

  if (visualization === "line-chart") {
    const leftTrendPixels = trendPixels(leftValues, domain, height);
    const rightTrendPixels = trendPixels(rightValues, domain, height);
    const diagnostics = {
      leftMinPixels: null,
      rightMinPixels: null,
      leftTrendPixels,
      rightTrendPixels,
    };
    const leftHidden =
      leftTrendPixels !== null &&
      leftTrendPixels < MIN_VISIBLE_TREND_PX &&
      rightTrendPixels !== null &&
      rightTrendPixels >= MIN_VISIBLE_TREND_PX;
    const rightHidden =
      rightTrendPixels !== null &&
      rightTrendPixels < MIN_VISIBLE_TREND_PX &&
      leftTrendPixels !== null &&
      leftTrendPixels >= MIN_VISIBLE_TREND_PX;
    if (!leftHidden && !rightHidden) return linearDecision(height, diagnostics);
    return {
      mode: compressedMode(leftValues, rightValues),
      constrainedSide: leftHidden ? "left" : "right",
      reason: "trend-below-visible-threshold",
      diagnostics: { drawableHeight: height, ...diagnostics },
    };
  }

  return linearDecision(height);
}

function paddedPositiveLogDomain(min, max) {
  const paddedMin = min / LOG_PADDING_FACTOR;
  const start = Number.isFinite(paddedMin) && paddedMin > 0 ? paddedMin : min;
  const paddedMax = max * LOG_PADDING_FACTOR;
  const end = Number.isFinite(paddedMax) ? paddedMax : max;
  if (start < end) return [start, end];

  const expandedEnd = max * 2;
  if (Number.isFinite(expandedEnd) && expandedEnd > max) return [start, expandedEnd];

  const reducedStart = max / 2;
  if (Number.isFinite(reducedStart) && reducedStart > 0 && reducedStart < max) {
    return [reducedStart, max];
  }
  return [Number.MIN_VALUE, Number.MAX_VALUE];
}

function adaptiveDomain(values, mode, fallbackDomain) {
  const numbers = finiteNumbers(values);
  const fallback = validDomain(fallbackDomain) || [0, 1];
  // Upstream owns the authoritative shared raw linear domain. Do not derive a replacement
  // from `values` here; trend-index callers must calculate and pass their index domain.
  if (mode === "linear" || !numbers.length) return fallback;
  if (mode === "log") {
    const positives = numbers.filter(value => value > 0);
    if (!positives.length) return fallback;
    const min = Math.min(...positives);
    const max = Math.max(...positives);
    return paddedPositiveLogDomain(min, max);
  }
  const min = Math.min(...numbers, fallback[0]);
  const max = Math.max(...numbers, fallback[1]);
  if (min === max) {
    const padding = Math.max(1, Math.abs(min) * 0.12);
    return [min - padding, max + padding];
  }
  return [min, max];
}

// Only symlog is pre-transformed here. Linear and log values remain unchanged; log callers
// must pass positive values and use a native logarithmic axis/domain.
function scaleValue(value, mode) {
  const number = optionalFiniteNumber(value);
  if (number === null) return null;
  if (mode !== "symlog") return number;
  return Math.sign(number) * Math.log1p(Math.abs(number) / SYMLOG_CONSTANT);
}

// This reverses only the explicit symlog pre-transform performed by scaleValue.
function unscaleValue(value, mode) {
  const number = optionalFiniteNumber(value);
  if (number === null) return null;
  if (mode !== "symlog") return number;
  return Math.sign(number) * SYMLOG_CONSTANT * Math.expm1(Math.abs(number));
}

function orderedTrendPoints(points = []) {
  const valid = (Array.isArray(points) ? points : [])
    .map((point, index) => ({
      ...point,
      value: optionalFiniteNumber(point?.value),
      __index: index,
      __year: optionalFiniteNumber(point?.year),
    }))
    .filter(point => point.value !== null);
  const hasComparableYears = valid.length > 1 && valid.every(point => point.__year !== null);
  return [...valid]
    .sort((left, right) =>
      hasComparableYears ? left.__year - right.__year : left.__index - right.__index
    )
    .map(({ __index, __year, ...point }) => point);
}

function trendChange(points = []) {
  const ordered = orderedTrendPoints(points);
  if (!ordered.length) {
    return {
      firstValue: null,
      lastValue: null,
      absoluteChange: null,
      percentChange: null,
      firstYear: null,
      lastYear: null,
    };
  }
  const first = ordered[0];
  const last = ordered[ordered.length - 1];
  const absoluteChange = last.value - first.value;
  return {
    firstValue: first.value,
    lastValue: last.value,
    absoluteChange,
    percentChange: first.value === 0 ? null : (absoluteChange / Math.abs(first.value)) * 100,
    firstYear: optionalFiniteNumber(first.year),
    lastYear: optionalFiniteNumber(last.year),
  };
}

function trendIndexPoints(points = []) {
  const ordered = orderedTrendPoints(points);
  if (!ordered.length || ordered[0].value === 0) return [];
  const baseline = ordered[0].value;
  return ordered.map(point => ({
    ...point,
    originalValue: point.value,
    value: (point.value / baseline) * 100,
  }));
}

module.exports = {
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
};
