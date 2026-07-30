const {
  adaptiveDomain,
  scaleValue,
  trendIndexPoints,
  unscaleValue,
} = require("./adaptiveChartScale");
const { formatAxisNumber } = require("./chartValueDisplay");
const {
  CHART_COLORS,
  CHART_LINE_WIDTH,
  categoryColor,
} = require("./chartTheme");

function optionalFiniteNumber(value) {
  if (
    value === null ||
    value === undefined ||
    (typeof value === "string" && value.trim() === "")
  ) {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function validDomain(domain) {
  if (!Array.isArray(domain) || domain.length !== 2) return null;
  const start = optionalFiniteNumber(domain[0]);
  const end = optionalFiniteNumber(domain[1]);
  if (start === null || end === null || start === end) return null;
  return start < end ? [start, end] : [end, start];
}

function linearScaleDecision(drawableHeight = 0) {
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
    },
  };
}

function visualizationForMode(mode) {
  if (mode === "line") return "line-chart";
  if (mode === "stacked") return "stacked-chart";
  if (["single", "bar"].includes(mode)) return "bar-chart";
  return null;
}

function finiteSeriesValues(series) {
  return (Array.isArray(series?.data) ? series.data : [])
    .map(point => optionalFiniteNumber(point?.value))
    .filter(value => value !== null);
}

function numericContextValues(values) {
  if (!Array.isArray(values)) return null;
  const numbers = values
    .map(optionalFiniteNumber)
    .filter(value => value !== null);
  return numbers.length === values.length ? numbers : null;
}

function equalValues(left, right) {
  return (
    Array.isArray(left) &&
    Array.isArray(right) &&
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

function validMergedScaleContext(data) {
  const expectedVisualization = visualizationForMode(data?.mode);
  const context = data?.scaleContext;
  const leftValues = numericContextValues(context?.leftValues);
  const rightValues = numericContextValues(context?.rightValues);
  const series = Array.isArray(data?.series) ? data.series : [];
  if (
    !expectedVisualization ||
    context?.adaptiveEligible === false ||
    context?.visualization !== expectedVisualization ||
    !validDomain(context?.domain) ||
    !leftValues ||
    !rightValues ||
    series.length < 2
  ) {
    return false;
  }
  return (
    equalValues(leftValues, finiteSeriesValues(series[0])) &&
    equalValues(rightValues, finiteSeriesValues(series[1]))
  );
}

function paddedDomain(values = []) {
  const numbers = (Array.isArray(values) ? values : [])
    .map(optionalFiniteNumber)
    .filter(value => value !== null);
  if (!numbers.length) return [0, 1];
  const min = Math.min(...numbers);
  const max = Math.max(...numbers);
  if (min === max) {
    const padding = Math.max(1, Math.abs(min) * 0.12);
    return [min - padding, max + padding];
  }
  const padding = (max - min) * 0.12;
  return [min - padding, max + padding];
}

function alignedTrendIndexPoints(points = []) {
  const source = Array.isArray(points) ? points : [];
  const indexed = trendIndexPoints(
    source.map((point, index) => ({ ...point, __mergedIndex: index }))
  );
  if (!indexed.length) return [];
  const indexedByPosition = new Map(
    indexed.map(point => [point.__mergedIndex, point])
  );
  return source.map((point, index) => {
    const indexedPoint = indexedByPosition.get(index);
    if (!indexedPoint) {
      return {
        ...point,
        value: null,
        originalValue: optionalFiniteNumber(point?.value),
      };
    }
    const { __mergedIndex, ...cleanPoint } = indexedPoint;
    return cleanPoint;
  });
}

function renderPoint(point, mode) {
  const originalValue = optionalFiniteNumber(point?.originalValue ?? point?.value);
  if (originalValue === null) {
    return { ...point, value: null, originalValue: null };
  }
  return {
    ...point,
    value: mode === "symlog" ? scaleValue(originalValue, "symlog") : originalValue,
    originalValue,
  };
}

function renderedSeriesForMode(data, mode) {
  const series = Array.isArray(data?.series) ? data.series : [];
  return series.map(item => {
    const source = mode === "index"
      ? alignedTrendIndexPoints(item.data)
      : (Array.isArray(item.data) ? item.data : []).map(point => renderPoint(point, mode));
    return { ...item, data: source };
  });
}

function sharedContextValues(data) {
  return [
    ...(Array.isArray(data?.scaleContext?.leftValues) ? data.scaleContext.leftValues : []),
    ...(Array.isArray(data?.scaleContext?.rightValues) ? data.scaleContext.rightValues : []),
  ]
    .map(optionalFiniteNumber)
    .filter(value => value !== null);
}

function buildMergedAdaptiveState({
  data = null,
  selectedScaleMode = "auto",
  scaleDecision = linearScaleDecision(),
} = {}) {
  const validScaleContext = validMergedScaleContext(data);
  const isLine = data?.mode === "line";
  const isSingle = data?.mode === "single";
  const isBar = ["single", "bar"].includes(data?.mode);
  const isStacked = data?.mode === "stacked";
  const decision = scaleDecision && typeof scaleDecision === "object"
    ? scaleDecision
    : linearScaleDecision();
  const adaptiveTriggered = Boolean(
    validScaleContext &&
    !isStacked &&
    ["log", "symlog"].includes(decision.mode)
  );
  const indexedSeries = isLine
    ? renderedSeriesForMode(data, "index")
    : [];
  const canUseTrendIndex = Boolean(
    isLine &&
    indexedSeries.length > 0 &&
    indexedSeries.every(series =>
      series.data.some(point => optionalFiniteNumber(point?.value) !== null)
    )
  );

  let resolvedScaleMode = "linear";
  if (adaptiveTriggered) {
    if (selectedScaleMode === "linear") resolvedScaleMode = "linear";
    else if (selectedScaleMode === "index" && canUseTrendIndex) resolvedScaleMode = "index";
    else resolvedScaleMode = decision.mode;
  }

  const sharedValues = validScaleContext ? sharedContextValues(data) : [];
  if (
    resolvedScaleMode === "log" &&
    (!sharedValues.length || sharedValues.some(value => value <= 0))
  ) {
    resolvedScaleMode = "symlog";
  }

  const renderedSeries = resolvedScaleMode === "index"
    ? indexedSeries
    : renderedSeriesForMode(data, resolvedScaleMode);
  const fallbackDomain = validDomain(data?.yDomain) || paddedDomain(
    (Array.isArray(data?.series) ? data.series : []).flatMap(finiteSeriesValues)
  );
  let rawDomain;
  if (isStacked) {
    rawDomain = [0, 100];
  } else if (resolvedScaleMode === "index") {
    rawDomain = paddedDomain(
      renderedSeries.flatMap(series =>
        series.data.map(point => optionalFiniteNumber(point?.value))
      )
    );
  } else if (validScaleContext && adaptiveTriggered) {
    rawDomain = adaptiveDomain(
      sharedValues,
      resolvedScaleMode,
      data.scaleContext.domain
    );
  } else if (validScaleContext) {
    rawDomain = validDomain(data.scaleContext.domain);
  } else {
    rawDomain = fallbackDomain;
  }

  const transformedDomain = resolvedScaleMode === "symlog"
    ? rawDomain.map(value => scaleValue(value, "symlog"))
    : rawDomain;
  const compressedBar = Boolean(
    isBar && ["log", "symlog"].includes(resolvedScaleMode)
  );
  const compressedSingle = Boolean(isSingle && compressedBar);

  return {
    validScaleContext,
    scaleDecision: decision,
    adaptiveTriggered,
    canUseTrendIndex,
    resolvedScaleMode,
    renderedSeries,
    rawDomain,
    transformedDomain,
    compressedBar,
    compressedSingle,
    seriesType: compressedBar ? "scatter" : isLine ? "line" : "bar",
  };
}


const AXIS_SPLIT_NUMBER = 4;

function formatMergedAxis(value, data) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  const domain = validDomain(data?.yDomain) || [0, 1];
  return formatAxisNumber(number, {
    min: domain[0],
    max: domain[1],
    splitNumber: AXIS_SPLIT_NUMBER,
    type: data?.unit === "%" ? "percentage" : "",
  });
}

function axisMeasureLabel(data) {
  const unit = String(data?.unit || "").trim();
  const basis = String(data?.basis || "").trim();
  if (!unit) return "";
  if (unit === "%" && basis) return `${basis} share (%)`;
  if (unit === "%") return "";
  return unit;
}

function shouldShowPointLabels(data, isLine) {
  if (!isLine) return true;
  return (data?.categories || []).length <= 16;
}

function pointLabelPosition(data, item) {
  if (data?.mode !== "single") return "top";
  const first = (Array.isArray(item?.data) ? item.data : []).find(point =>
    optionalFiniteNumber(point?.originalValue ?? point?.value) !== null
  );
  const originalValue = optionalFiniteNumber(first?.originalValue ?? first?.value);
  return originalValue !== null && originalValue < 0 ? "bottom" : "top";
}

function buildStandardSeries(data, state, colors) {
  return (Array.isArray(state?.renderedSeries) ? state.renderedSeries : []).map(
    (item, index) => ({
      name: item.name,
      type: state.seriesType,
      smooth: false,
      symbol: ["line", "scatter"].includes(state.seriesType) ? "circle" : "none",
      symbolSize: state.seriesType === "scatter" ? 12 : 8,
      barMaxWidth: data?.mode === "single" ? 42 : 28,
      barGap: "14%",
      data: (Array.isArray(item.data) ? item.data : []).map(point => ({
        value: point.value,
        originalValue: point.originalValue ?? point.value,
        display: point.display,
        raw: point.raw,
      })),
      label: {
        show: shouldShowPointLabels(data, state.seriesType === "line"),
        position: pointLabelPosition(data, item),
        distance: 8,
        color: "#243447",
        fontSize: 11,
        formatter: params => params.data?.display || "-",
      },
      lineStyle: { width: CHART_LINE_WIDTH },
      itemStyle: {
        color: colors[index % colors.length],
        borderRadius: state.seriesType === "bar" ? [4, 4, 0, 0] : 0,
      },
    })
  );
}

function buildStackedSeries(data) {
  const categories = Array.isArray(data?.categories) ? data.categories : [];
  const sourceSeries = Array.isArray(data?.series) ? data.series : [];
  return categories.map((category, categoryIndex) => ({
    name: category,
    type: "bar",
    stack: "total",
    barMaxWidth: 72,
    data: sourceSeries.map(side => {
      const points = Array.isArray(side?.data) ? side.data : [];
      const point = points[categoryIndex] || {};
      const total = points.reduce((sum, item) => {
        const value = optionalFiniteNumber(item?.value);
        return value !== null && value > 0 ? sum + value : sum;
      }, 0);
      const renderTotal = total > 101 ? total : 100;
      const value = optionalFiniteNumber(point?.value);
      const percent = renderTotal && value !== null && value > 0
        ? (value / renderTotal) * 100
        : null;
      return {
        value: percent,
        display: point.display,
        raw: point.raw,
      };
    }),
    label: { show: false },
    emphasis: { focus: "series" },
  }));
}

function buildMergedComparisonOption({ data = {}, state = {}, grid = {} } = {}) {
  const isLine = data.mode === "line";
  const isStacked = data.mode === "stacked";
  const categories = Array.isArray(data.categories) ? data.categories : [];
  const colors = [CHART_COLORS[0], CHART_COLORS[1]];
  const transformedDomain = validDomain(state.transformedDomain) || [0, 1];
  const series = isStacked
    ? buildStackedSeries(data)
    : buildStandardSeries(data, state, colors);

  return {
    color: isStacked
      ? categories.map((category, index) => categoryColor(category, index))
      : colors,
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: isLine || state.compressedBar ? "line" : "shadow",
      },
      formatter: params => (Array.isArray(params) ? params : [params])
        .filter(Boolean)
        .map(param => {
          const display = param.data?.display || "-";
          return `${param.marker || ""}${param.seriesName}: ${display}`;
        })
        .join("<br/>"),
    },
    legend: {
      top: 0,
      left: "center",
      icon: "roundRect",
      itemWidth: 14,
      itemHeight: 8,
      textStyle: { color: "#334155", fontSize: 12 },
    },
    grid,
    xAxis: {
      type: "category",
      data: isStacked
        ? (Array.isArray(data.series) ? data.series : []).map(item => item.name)
        : categories,
      axisTick: { alignWithLabel: true },
      axisLabel: {
        interval: 0,
        rotate: categories.length > 4 && !isStacked ? 24 : 0,
        color: "#475569",
        fontSize: 11,
        hideOverlap: true,
      },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
    },
    yAxis: {
      type: state.resolvedScaleMode === "log" ? "log" : "value",
      min: transformedDomain[0],
      max: transformedDomain[1],
      splitNumber: AXIS_SPLIT_NUMBER,
      name: axisMeasureLabel(data),
      ...(state.resolvedScaleMode === "index"
        ? { name: "趋势指数（首值=100）" }
        : {}),
      nameLocation: "middle",
      nameGap: 42,
      nameTextStyle: {
        color: "#475569",
        fontSize: 11,
        fontWeight: 600,
      },
      axisLabel: {
        color: "#475569",
        formatter: value => {
          if (isStacked) return `${value}%`;
          if (state.resolvedScaleMode === "index") return Number(value).toFixed(0);
          const original = state.resolvedScaleMode === "symlog"
            ? unscaleValue(value, "symlog")
            : value;
          const nearestInteger = Math.round(original);
          const displayValue = Math.abs(original - nearestInteger) <=
            Number.EPSILON * Math.max(1, Math.abs(original)) * 8
            ? nearestInteger
            : original;
          return formatMergedAxis(displayValue, { ...data, yDomain: state.rawDomain });
        },
      },
      splitLine: { lineStyle: { color: "#e5eaf1" } },
      axisLine: { show: false },
    },
    series,
    dataZoom: [],
  };
}

module.exports = {
  alignedTrendIndexPoints,
  buildMergedComparisonOption,
  buildMergedAdaptiveState,
  linearScaleDecision,
  paddedDomain,
  validMergedScaleContext,
};
