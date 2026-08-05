const {
  adaptiveDomain,
  detectAdaptiveScale,
  scaleValue,
  trendIndexPoints,
  unscaleValue,
} = require("./adaptiveChartScale");
const {
  barChartDomain,
  categoryLabelForPoint,
  formatAxisNumber,
  shortValueText,
  xLabelForPoint,
} = require("./chartValueDisplay");
const { CHART_COLORS, CHART_LINE_WIDTH } = require("./chartTheme");

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

function canonicalAdaptiveContextEnabled({
  scaleContext,
  side,
  visualization,
  dataLength,
} = {}) {
  const values =
    side === "left"
      ? scaleContext?.leftValues
      : side === "right"
        ? scaleContext?.rightValues
        : null;
  const alignedValues =
    Number.isInteger(dataLength) &&
    dataLength >= 0 &&
    Array.isArray(values) &&
    values.length === dataLength;
  if (alignedValues) {
    for (let index = 0; index < dataLength; index += 1) {
      if (!Object.prototype.hasOwnProperty.call(values, index) || values[index] === undefined) {
        return false;
      }
    }
  }
  return Boolean(
    scaleContext?.decisionStatus === "pending" &&
      scaleContext?.valueSpace === "normalized-base" &&
      ["left", "right"].includes(side) &&
      ["bar-chart", "line-chart"].includes(visualization) &&
      alignedValues
  );
}

function contextValuesForSide(scaleContext, side) {
  if (!["left", "right"].includes(side)) return [];
  const values = scaleContext?.[side === "right" ? "rightValues" : "leftValues"];
  return Array.isArray(values) ? values.map(optionalFiniteNumber) : [];
}

function sharedContextValues(scaleContext) {
  return [
    ...(Array.isArray(scaleContext?.leftValues) ? scaleContext.leftValues : []),
    ...(Array.isArray(scaleContext?.rightValues) ? scaleContext.rightValues : []),
  ]
    .map(optionalFiniteNumber)
    .filter(value => value !== null);
}

function plotDataForContext({ data, scaleContext, side, visualization } = {}) {
  const source = Array.isArray(data) ? data : [];
  const canonicalAdaptiveEnabled = canonicalAdaptiveContextEnabled({
    scaleContext,
    side,
    visualization,
    dataLength: source.length,
  });
  if (!canonicalAdaptiveEnabled) {
    return source
      .filter(item => optionalFiniteNumber(item?.value) !== null)
      .map(item => ({
        ...item,
        value: optionalFiniteNumber(item.value),
        originalValue: optionalFiniteNumber(item.value),
      }));
  }
  const values = contextValuesForSide(scaleContext, side);
  return source
    .map((item, index) => ({
      ...item,
      value: values[index],
      originalValue: values[index],
    }))
    .filter(item => item.value !== null && item.value !== undefined);
}

function orderedLinePoints(points = []) {
  const source = Array.isArray(points) ? points : [];
  const years = source.map(point => optionalFiniteNumber(point?.year));
  const hasComparableYears = source.length > 1 && years.every(year => year !== null);
  if (!hasComparableYears) return [...source];
  return source
    .map((point, index) => ({ point, year: years[index], index }))
    .sort((left, right) => left.year - right.year || left.index - right.index)
    .map(entry => entry.point);
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

function validDomain(domain) {
  if (!Array.isArray(domain) || domain.length !== 2) return null;
  const start = optionalFiniteNumber(domain[0]);
  const end = optionalFiniteNumber(domain[1]);
  if (start === null || end === null || start === end) return null;
  return start < end ? [start, end] : [end, start];
}

function renderDataForMode(data, mode) {
  if (mode === "index") return trendIndexPoints(data);
  return data.map(item => ({
    ...item,
    originalValue: item.originalValue ?? item.value,
    value: mode === "symlog" ? scaleValue(item.value, "symlog") : item.value,
  }));
}

function tooltipLineForParam(param = {}) {
  const display = param.data?.display || param.data?.originalDisplay || "-";
  return `${param.marker || ""}${param.name || ""}: ${display}`;
}

function labelValueForParam(param = {}) {
  return (
    param.data?.shortDisplay ||
    param.data?.display ||
    param.data?.originalDisplay ||
    "-"
  );
}

function buildAdaptiveChartState({
  data = [],
  scaleContext = null,
  side = "",
  visualization = "",
  selectedScaleMode = "auto",
  drawableHeight = 0,
  localDomain = null,
} = {}) {
  const source = Array.isArray(data) ? data : [];
  const canonicalAdaptiveEnabled = canonicalAdaptiveContextEnabled({
    scaleContext,
    side,
    visualization,
    dataLength: source.length,
  });
  const plotData = plotDataForContext({
    data: source,
    scaleContext,
    side,
    visualization,
  });
  const orderedData = visualization === "line-chart" ? orderedLinePoints(plotData) : plotData;
  const decision =
    canonicalAdaptiveEnabled && plotData.length
      ? detectAdaptiveScale({
          leftValues: scaleContext.leftValues,
          rightValues: scaleContext.rightValues,
          domain: scaleContext.domain,
          drawableHeight,
          visualization,
        })
      : linearScaleDecision(drawableHeight);
  const adaptiveTriggered =
    canonicalAdaptiveEnabled &&
    plotData.length > 0 &&
    ["log", "symlog"].includes(decision.mode);
  const indexData = visualization === "line-chart" ? trendIndexPoints(orderedData) : [];
  const canUseTrendIndex = indexData.length > 0;

  let resolvedScaleMode = "linear";
  if (adaptiveTriggered) {
    if (selectedScaleMode === "linear") resolvedScaleMode = "linear";
    else if (selectedScaleMode === "index" && canUseTrendIndex) resolvedScaleMode = "index";
    else resolvedScaleMode = decision.mode;
  }

  const renderedData =
    resolvedScaleMode === "index" ? indexData : renderDataForMode(orderedData, resolvedScaleMode);
  const fallbackDomain =
    validDomain(localDomain) || paddedDomain(orderedData.map(item => item.value));
  let rawDomain = fallbackDomain;
  if (resolvedScaleMode === "index") {
    rawDomain = paddedDomain(renderedData.map(item => item.value));
  } else if (adaptiveTriggered) {
    rawDomain = adaptiveDomain(
      sharedContextValues(scaleContext),
      resolvedScaleMode,
      scaleContext?.domain || fallbackDomain
    );
  }

  return {
    canonicalAdaptiveEnabled,
    plotData,
    orderedData,
    decision,
    adaptiveTriggered,
    canUseTrendIndex,
    resolvedScaleMode,
    renderedData,
    rawDomain,
  };
}

const AXIS_SPLIT_NUMBER = 4;

function fullChartGrid(dataLength, visualization) {
  const count = Math.max(0, Number(dataLength) || 0);
  const expanded = visualization === "line-chart" ? count > 6 : count > 5;
  return {
    top: 34,
    left: 60,
    right: 28,
    bottom: expanded ? (visualization === "line-chart" ? 72 : 76) : 48,
    containLabel: true,
  };
}

function resolvedDrawableHeight({ drawableHeight, chartHeight, grid }) {
  const explicit = Number(drawableHeight);
  if (Number.isFinite(explicit) && explicit >= 0) return explicit;
  const height = Number(chartHeight);
  if (!Number.isFinite(height)) return 0;
  return Math.max(0, height - Number(grid?.top || 0) - Number(grid?.bottom || 0));
}

function formatFullChartAxisValue(value, rawDomain, axisType) {
  return formatAxisNumber(value, {
    min: rawDomain[0],
    max: rawDomain[1],
    splitNumber: AXIS_SPLIT_NUMBER,
    type: axisType,
  });
}

function fullChartAxisForScale(mode, rawDomain, axisType) {
  if (mode === "log") {
    return {
      type: "log",
      min: rawDomain[0],
      max: rawDomain[1],
      axisLabel: {
        color: "#475569",
        formatter: value => formatFullChartAxisValue(value, rawDomain, axisType),
      },
    };
  }
  if (mode === "symlog") {
    const transformedDomain = rawDomain.map(value => scaleValue(value, "symlog"));
    return {
      type: "value",
      min: transformedDomain[0],
      max: transformedDomain[1],
      axisLabel: {
        color: "#475569",
        formatter: value =>
          formatFullChartAxisValue(unscaleValue(value, "symlog"), rawDomain, axisType),
      },
    };
  }
  return {
    type: "value",
    min: rawDomain[0],
    max: rawDomain[1],
    axisLabel: {
      color: "#475569",
      formatter: value => formatFullChartAxisValue(value, rawDomain, axisType),
    },
  };
}

function fullChartYAxis(axis, axisUnitLabel) {
  return {
    ...axis,
    splitNumber: AXIS_SPLIT_NUMBER,
    name: axisUnitLabel || "",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: {
      color: "#475569",
      fontSize: 11,
      fontWeight: 600,
    },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: "#e5eaf1" } },
  };
}

function fullChartTooltip({ shadowPointer = false } = {}) {
  return {
    trigger: "axis",
    ...(shadowPointer ? { axisPointer: { type: "shadow" } } : {}),
    formatter: params => (Array.isArray(params) ? params : [params])
      .filter(Boolean)
      .map(param => tooltipLineForParam(param))
      .join("<br/>"),
  };
}

function fullChartShortDisplay(item, axisType) {
  return shortValueText(
    { ...item, value: item.originalValue ?? item.value },
    axisType
  );
}

function buildFullChartBarOption({
  data = [],
  scaleContext = null,
  side = "",
  selectedScaleMode = "auto",
  drawableHeight,
  chartHeight,
  fieldKey = "",
  axisType = "",
  axisUnitLabel = "",
  colors = CHART_COLORS,
} = {}) {
  const source = Array.isArray(data) ? data : [];
  const plotData = plotDataForContext({
    data: source,
    scaleContext,
    side,
    visualization: "bar-chart",
  });
  const grid = fullChartGrid(plotData.length, "bar-chart");
  const state = buildAdaptiveChartState({
    data: source,
    scaleContext,
    side,
    visualization: "bar-chart",
    selectedScaleMode,
    drawableHeight: resolvedDrawableHeight({ drawableHeight, chartHeight, grid }),
    localDomain: barChartDomain(plotData.map(item => item.value)),
  });
  const mode = state.resolvedScaleMode;
  const rendered = state.renderedData;
  const rawDomain = state.rawDomain;
  const axis = fullChartAxisForScale(mode, rawDomain, axisType);
  const compressed = ["log", "symlog"].includes(mode);
  const [min, max] = rawDomain;
  const option = {
    color: colors,
    tooltip: fullChartTooltip({ shadowPointer: true }),
    grid,
    xAxis: {
      type: "category",
      data: rendered.map((item, index) => categoryLabelForPoint(item, index, {
        fallback: fieldKey,
        total: rendered.length,
      })),
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
      axisLabel: {
        interval: 0,
        rotate: rendered.length > 5 ? 28 : 0,
        color: "#475569",
        fontSize: 11,
        overflow: "truncate",
        width: 90,
      },
    },
    yAxis: fullChartYAxis(axis, axisUnitLabel),
    series: [{
      type: compressed ? "scatter" : "bar",
      symbolSize: compressed ? 12 : undefined,
      barMaxWidth: compressed ? undefined : (rendered.length === 1 ? 28 : 54),
      data: rendered.map((item, index) => ({
        value: item.value,
        originalValue: item.originalValue ?? item.value,
        display: item.display,
        originalDisplay: item.originalDisplay,
        shortDisplay: fullChartShortDisplay(item, axisType),
        itemStyle: {
          color: colors[index % colors.length],
          borderRadius: compressed
            ? 0
            : item.value >= 0
              ? [4, 4, 0, 0]
              : [0, 0, 4, 4],
        },
      })),
      label: {
        show: true,
        position: "top",
        color: "#1f2937",
        fontSize: 11,
        formatter: params => labelValueForParam(params),
      },
      markLine: !compressed && min < 0 && max > 0
        ? {
            silent: true,
            symbol: "none",
            lineStyle: { color: "#94a3b8", type: "dashed", width: 1 },
            data: [{ yAxis: 0 }],
          }
        : undefined,
    }],
    dataZoom: rendered.length > 10
      ? [{
          type: "slider",
          height: 18,
          bottom: 14,
          start: 0,
          end: Math.min(100, (10 / rendered.length) * 100),
        }]
      : [],
  };
  return { option, state, grid };
}

function buildFullChartLineOption({
  data = [],
  scaleContext = null,
  side = "",
  selectedScaleMode = "auto",
  drawableHeight,
  chartHeight,
  fieldKey = "",
  axisType = "",
  axisUnitLabel = "",
  colors = CHART_COLORS,
} = {}) {
  const source = Array.isArray(data) ? data : [];
  const localData = orderedLinePoints(plotDataForContext({
    data: source,
    scaleContext,
    side,
    visualization: "line-chart",
  }));
  const grid = fullChartGrid(localData.length, "line-chart");
  const state = buildAdaptiveChartState({
    data: source,
    scaleContext,
    side,
    visualization: "line-chart",
    selectedScaleMode,
    drawableHeight: resolvedDrawableHeight({ drawableHeight, chartHeight, grid }),
    localDomain: paddedDomain(localData.map(item => item.value)),
  });
  const dataPoints = state.orderedData;
  const mode = state.resolvedScaleMode;
  const rendered = state.renderedData;
  const rawDomain = state.rawDomain;
  const axis = fullChartAxisForScale(mode === "index" ? "linear" : mode, rawDomain, axisType);
  const option = {
    color: [colors[0]],
    tooltip: fullChartTooltip(),
    grid,
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: dataPoints.map((item, index) => xLabelForPoint(item, index)),
      axisLabel: {
        interval: 0,
        rotate: dataPoints.length > 6 ? 24 : 0,
        color: "#475569",
        fontSize: 11,
      },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
    },
    yAxis: fullChartYAxis(axis, axisUnitLabel),
    series: [{
      type: "line",
      smooth: false,
      symbol: "circle",
      symbolSize: 8,
      data: rendered.map(item => ({
        value: item.value,
        originalValue: item.originalValue ?? item.value,
        display: item.display,
        originalDisplay: item.originalDisplay,
        shortDisplay: mode === "index"
          ? `${Number(item.value).toFixed(1)}`
          : fullChartShortDisplay(item, axisType),
      })),
      lineStyle: { width: CHART_LINE_WIDTH },
      label: {
        show: dataPoints.length <= 8 || ["log", "symlog"].includes(mode),
        position: "top",
        color: "#1f2937",
        fontSize: 11,
        formatter: params => {
          if (
            ["log", "symlog"].includes(mode) &&
            params.dataIndex !== 0 &&
            params.dataIndex !== rendered.length - 1
          ) {
            return "";
          }
          return labelValueForParam(params);
        },
      },
    }],
    dataZoom: dataPoints.length > 12
      ? [{
          type: "slider",
          height: 18,
          bottom: 14,
          start: 0,
          end: Math.min(100, (12 / dataPoints.length) * 100),
        }]
      : [],
  };
  return { option, state, grid };
}

module.exports = {
  buildAdaptiveChartState,
  buildFullChartBarOption,
  buildFullChartLineOption,
  canonicalAdaptiveContextEnabled,
  contextValuesForSide,
  labelValueForParam,
  linearScaleDecision,
  orderedLinePoints,
  paddedDomain,
  plotDataForContext,
  sharedContextValues,
  tooltipLineForParam,
};
