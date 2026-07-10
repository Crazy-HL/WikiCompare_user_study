const MAGNITUDE_WORDS =
	"(?:quadrillion|trillion|billion|million|thousand|percent)";
const NUMBER_DISPLAY = String.raw`(?:US\$|[$¥₩€£])?\s*[+-]?\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th)?\s*(?:${MAGNITUDE_WORDS}|%)?`;

function escapeRegExp(value) {
	return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeSource(value) {
	return String(value || "")
		.replace(/\u00a0/g, " ")
		.replace(/\s+/g, " ")
		.trim();
}

function trimFixed(value, digits = 2) {
	return Number(value)
		.toFixed(digits)
		.replace(/\.0+$/, "")
		.replace(/(\.\d*[1-9])0+$/, "$1");
}

function normalizedChartType(type = "") {
	const normalized = String(type || "").trim().toLowerCase();
	if (
		normalized === "percentage" ||
		normalized === "percent" ||
		normalized === "proportional" ||
		normalized.includes("percent")
	) {
		return "percentage";
	}
	return normalized;
}

function inferredChartType(dataType = "", label = "", source = "") {
	const normalized = normalizedChartType(dataType);
	if (normalized === "percentage") return normalized;
	const text = `${label} ${source}`.toLowerCase();
	if (/(^|\s|[(:])%|percent|percentage/.test(text)) return "percentage";
	if (/\b(?:real\s+gdp|gdp|economic)?\s*growth\s+rate\b/.test(text)) {
		return "percentage";
	}
	if (/\b(?:unemployment|inflation)\s+rate\b/.test(text)) return "percentage";
	return normalized;
}

function formatChartNumber(value, type = "") {
	const num = Number(value);
	if (!Number.isFinite(num)) return "-";
	if (normalizedChartType(type) === "percentage") return `${num.toFixed(1)}%`;

	const abs = Math.abs(num);
	if (abs >= 1e12) return `${trimFixed(num / 1e12)}T`;
	if (abs >= 1e9) return `${trimFixed(num / 1e9)}B`;
	if (abs >= 1e6) return `${trimFixed(num / 1e6)}M`;
	if (abs >= 1e3) return `${trimFixed(num / 1e3)}K`;
	return trimFixed(num, Math.abs(num) < 10 ? 1 : 0);
}

function axisPrecisionForSpan(span, type = "") {
	const safeSpan = Math.abs(Number(span));
	if (!Number.isFinite(safeSpan) || safeSpan <= 0) return 1;
	if (type === "percentage") {
		if (safeSpan >= 20) return 0;
		if (safeSpan >= 1) return 1;
		if (safeSpan >= 0.01) return 2;
		if (safeSpan >= 0.001) return 3;
		return 4;
	}
	if (safeSpan >= 20) return 0;
	if (safeSpan >= 1) return 1;
	if (safeSpan >= 0.01) return 2;
	if (safeSpan >= 0.001) return 3;
	return 4;
}

function decimalPlacesForStep(step) {
	const safeStep = Math.abs(Number(step));
	if (!Number.isFinite(safeStep) || safeStep <= 0) return null;
	for (let digits = 0; digits <= 6; digits += 1) {
		const scaled = safeStep * (10 ** digits);
		if (Math.abs(scaled - Math.round(scaled)) < 1e-8) return digits;
	}
	return 6;
}

function axisStepFromOptions(options, span) {
	if (Array.isArray(options.tickValues)) {
		const ticks = [...new Set(
			options.tickValues.map(Number).filter(Number.isFinite)
		)].sort((a, b) => a - b);
		const steps = ticks
			.slice(1)
			.map((tick, index) => Math.abs(tick - ticks[index]))
			.filter(step => step > 0);
		if (steps.length) return Math.min(...steps);
	}

	const tickStep = Math.abs(Number(options.tickStep));
	if (Number.isFinite(tickStep) && tickStep > 0) return tickStep;

	const splitNumber = Number(options.splitNumber);
	if (Number.isFinite(splitNumber) && splitNumber > 0 && span > 0) {
		return span / splitNumber;
	}

	return null;
}

function formatAxisNumber(value, options = {}) {
	const num = Number(value);
	if (!Number.isFinite(num)) return String(value);
	const type = normalizedChartType(options.type);
	const min = Number(options.min);
	const max = Number(options.max);
	const span = Number.isFinite(min) && Number.isFinite(max)
		? Math.abs(max - min)
		: Math.abs(num);
	const step = axisStepFromOptions(options, span);

	if (type === "percentage") {
		const digits = step === null
			? axisPrecisionForSpan(span, type)
			: decimalPlacesForStep(step);
		return `${num.toFixed(digits)}%`;
	}

	const abs = Math.abs(num);
	const scale =
		abs >= 1e12 ? { divisor: 1e12, suffix: "T" } :
		abs >= 1e9 ? { divisor: 1e9, suffix: "B" } :
		abs >= 1e6 ? { divisor: 1e6, suffix: "M" } :
		abs >= 1e3 ? { divisor: 1e3, suffix: "K" } :
		null;
	if (scale) {
		const scaledSpan = span / scale.divisor;
		const scaledStep = step === null ? null : step / scale.divisor;
		const digits = scaledStep === null
			? scaledSpan >= 100 ? 0 : scaledSpan >= 10 ? 1 : 2
			: decimalPlacesForStep(scaledStep);
		return `${trimFixed(num / scale.divisor, digits)}${scale.suffix}`;
	}

	const digits = step === null
		? axisPrecisionForSpan(span, type)
		: decimalPlacesForStep(step);
	return num.toFixed(digits);
}

function cleanChartText(value) {
	return String(value || "")
		.replace(/\u00a0/g, " ")
		.replace(/\s+/g, " ")
		.trim();
}

function cleanLegendCategoryText(value) {
	return cleanChartText(value)
		.replace(/\s*:\s*(?:US\$|[$¥₩€£])?\s*[+-]?\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th)?\s*(?:quadrillion|trillion|billion|million|thousand|percent|%)?.*$/i, "")
		.replace(/\s+\((?:est\.?|estimate|estimated)?\s*[12]\d{3}\s*(?:est\.?)?\)$/i, "")
		.replace(/\s+/g, " ")
		.trim();
}

function isUnitLikeCategoryLabel(label) {
	const text = cleanChartText(label).toLowerCase();
	if (!text) return false;
	if (/^%(\s+of\s+[\w\s]+)?$/.test(text)) return true;
	if (/^(?:percent|percentage)(?:\s+of\s+[\w\s]+)?$/.test(text)) return true;
	if (/^(?:rate|share|value|amount|score|index)$/i.test(text)) return true;
	return false;
}

function isGenericPieCategoryLabel(label) {
	const text = cleanChartText(label).toLowerCase();
	return /^(?:years?|years and over|age|ages)$/.test(text);
}

function titleCaseLegendText(value) {
	const text = cleanLegendCategoryText(value);
	if (!text) return "";
	const special = text
		.replace(/\bgdp\b/gi, "GDP")
		.replace(/\busd\b/gi, "USD")
		.replace(/\bppp\b/gi, "PPP");
	if (/[A-Z]/.test(special.slice(1))) return special;
	if (/^[%0-9]/.test(special)) return special;
	return special.charAt(0).toUpperCase() + special.slice(1);
}

function pieLegendLabelForPoint(point, index, options = {}) {
	const label = cleanChartText(point?.label);
	const year = cleanChartText(point?.year);
	const fallback = cleanChartText(options.fallback);
	const total = Number(options.total || 0);
	const raw = cleanChartText(point?.display || point?.raw || point?.rawText);
	const rawLabel = cleanLegendCategoryText(raw);
	if (
		isGenericPieCategoryLabel(label)
	) {
		const ageIndex = total > 3 && index > 0 ? index - 1 : index;
		return ["0-14 years", "15-64 years", "65 years and over"][ageIndex] || label;
	}
	if (year && (!label || label === year || isUnitLikeCategoryLabel(label))) {
		return year;
	}
	if (
		label &&
		isGenericPieCategoryLabel(label) &&
		rawLabel &&
		rawLabel.toLowerCase() !== label.toLowerCase()
	) {
		return titleCaseLegendText(rawLabel);
	}
	if (label && label !== year && !looksLikeValueDisplay(label)) {
		return titleCaseLegendText(label);
	}

	if (rawLabel && !isUnitLikeCategoryLabel(rawLabel) && !looksLikeValueDisplay(rawLabel)) {
		return titleCaseLegendText(rawLabel);
	}
	if (year) return year;
	if (fallback && total <= 1) return titleCaseLegendText(fallback);
	return fallback ? titleCaseLegendText(fallback) : String(index + 1);
}

function compactMiddleText(text, maxChars = 16) {
	const value = cleanChartText(text);
	const limit = Math.max(4, Number(maxChars) || 16);
	if (value.length <= limit) return value;
	const suffixLength = Math.max(4, Math.min(8, Math.floor(limit * 0.45)));
	const prefixLength = Math.max(2, limit - suffixLength - 1);
	return `${value.slice(0, prefixLength)}…${value.slice(-suffixLength)}`;
}

function isYearOnlyMeasurementText(text, point) {
	const numericValue = point && point.value !== undefined ? Number(point.value) : NaN;
	if (!Number.isFinite(numericValue)) return false;
	const normalized = cleanChartText(text)
		.replace(/^\(+|\)+$/g, "")
		.replace(/\b(?:est\.?|estimate|estimated)\b/gi, "")
		.replace(/[.;,\s]/g, "");
	const yearMatch = normalized.match(/^[12]\d{3}$/);
	if (!yearMatch) return false;
	return numericValue !== Number(yearMatch[0]);
}

function isPlainNumericText(text) {
	const normalized = cleanChartText(text).replace(/,/g, "");
	return /^[+-]?\d+(?:\.\d+)?$/.test(normalized);
}

function plainNumericMatchesPoint(text, point) {
	if (!isPlainNumericText(text)) return false;
	const numericValue = point && point.value !== undefined ? Number(point.value) : NaN;
	if (!Number.isFinite(numericValue)) return false;
	return Math.abs(Number(cleanChartText(text).replace(/,/g, "")) - numericValue) < 1e-9;
}

function looksLikeValueDisplay(label) {
	const text = cleanChartText(label);
	if (!text) return false;
	if (/:\s*(?:US\$|[$¥₩€£])?\s*[+-]?\d/i.test(text)) return true;
	if (/:\s*[+-]?\d[\d,]*(?:\.\d+)?\s*(?:%|percent|million|billion|trillion|thousand)?/i.test(text)) return true;
	return false;
}

function displayTextForPoint(point) {
	if (!point) return "-";
	const display = cleanChartText(point.display);
	if (display && !isYearOnlyMeasurementText(display, point)) return display;
	const raw = cleanChartText(point.raw);
	if (raw && !isYearOnlyMeasurementText(raw, point)) return raw;
	return cleanChartText(point.value || "-");
}

function shortValueText(point, type = "") {
	const display = displayTextForPoint(point);
	const colonIndex = display.lastIndexOf(":");
	if (colonIndex >= 0) {
		const valueText = display.slice(colonIndex + 1).trim();
		if (
			isYearOnlyMeasurementText(valueText, point) ||
			(normalizedChartType(type) === "percentage" && plainNumericMatchesPoint(valueText, point))
		) {
			return formatChartNumber(point?.value, type);
		}
		return valueText;
	}
	if (isYearOnlyMeasurementText(display, point)) {
		return formatChartNumber(point?.value, type);
	}
	if (
		normalizedChartType(type) === "percentage" &&
		plainNumericMatchesPoint(display, point)
	) {
		return formatChartNumber(point?.value, type);
	}
	return display || formatChartNumber(point?.value, type);
}

function categoryLabelForPoint(point, index, options = {}) {
	const label = cleanChartText(point?.label);
	const year = cleanChartText(point?.year);
	const fallback = cleanChartText(options.fallback);
	const total = Number(options.total || 0);
	if (label && label !== year && !looksLikeValueDisplay(label)) return label;
	if (year) return year;
	if (fallback && total <= 1) return fallback;
	if (label && !looksLikeValueDisplay(label)) return label;
	return fallback || String(index + 1);
}

function barChartDomain(values) {
	const nums = (values || []).map(Number).filter(Number.isFinite);
	if (!nums.length) return [0, 1];
	const min = Math.min(...nums);
	const max = Math.max(...nums);
	if (min < 0 && max <= 0) {
		const bound = Math.abs(min) * 1.1;
		return [
			Number((-bound).toFixed(12)),
			Number(bound.toFixed(12)),
		];
	}
	if (min >= 0 && max > 0) return [0, Number((max * 1.1).toFixed(12))];
	const padding = (max - min) * 0.08 || 1;
	return [
		Number((min - padding).toFixed(12)),
		Number((max + padding).toFixed(12)),
	];
}

function findNumberNearLabel(source, label) {
	if (!label) return "";
	const labelPattern = escapeRegExp(label).replace(/\\ /g, "\\s+");
	const categoryPattern = new RegExp(
		String.raw`\b${labelPattern}:?\s*(${NUMBER_DISPLAY})`,
		"gi"
	);
	for (const categoryMatch of source.matchAll(categoryPattern)) {
		if (isCategoryBoundary(source, categoryMatch.index || 0)) {
			return normalizeSource(categoryMatch[1]);
		}
	}

	const labelIndex = source.toLowerCase().indexOf(String(label).toLowerCase());
	if (labelIndex >= 0) {
		const before = source.slice(Math.max(0, labelIndex - 80), labelIndex);
		const after = source.slice(labelIndex, labelIndex + 80);
		if (/^\s*[^:]{0,45}:\s*/.test(after)) {
			const afterMatch = after.match(new RegExp(NUMBER_DISPLAY, "i"));
			if (afterMatch) return normalizeSource(afterMatch[0]);
		}
		const measuredAfterMatch = after.match(
			new RegExp(
				String.raw`\b(?:totaled|was|were|reached|rose\s+to|achieved|crossed|passed)\b[^.;,]*?(${NUMBER_DISPLAY})`,
				"i"
			)
		);
		if (measuredAfterMatch) return normalizeSource(measuredAfterMatch[1]);
		const beforeMatches = [...before.matchAll(new RegExp(NUMBER_DISPLAY, "gi"))];
		if (beforeMatches.length) {
			return normalizeSource(beforeMatches[beforeMatches.length - 1][0]);
		}
		const afterMatch = after.match(new RegExp(NUMBER_DISPLAY, "i"));
		if (afterMatch) return normalizeSource(afterMatch[0]);
	}
	return "";
}

function isCategoryBoundary(source, startIndex) {
	const prefix = source.slice(0, startIndex);
	const lastPercent = prefix.lastIndexOf("%");
	const lastComma = prefix.lastIndexOf(",");
	const lastSemicolon = prefix.lastIndexOf(";");
	const lastLine = prefix.lastIndexOf("\n");
	const boundary = Math.max(lastPercent, lastComma, lastSemicolon, lastLine);
	const betweenBoundaryAndLabel = prefix.slice(boundary + 1).trim();
	return !/[A-Za-z]/.test(betweenBoundaryAndLabel);
}

function findNumberWithContext(source, label, year) {
	if (!source) return "";

	if (label && year) {
		const labelPattern = escapeRegExp(label).replace(/\\ /g, "\\s+");
		const pattern = new RegExp(
			String.raw`(${NUMBER_DISPLAY})\s*\([^)]*${labelPattern}[^)]*${year}[^)]*\)`,
			"i"
		);
		const match = source.match(pattern);
		if (match) return normalizeSource(match[1]);
	}

	const currencyNumber = findCurrencyNumber(source, label, year);
	if (currencyNumber) return currencyNumber;

	const labeledNumber = findNumberNearLabel(source, label);
	if (labeledNumber) return labeledNumber;

	if (year) {
		const pattern = new RegExp(
			String.raw`(${NUMBER_DISPLAY})\s*\([^)]*${year}[^)]*\)`,
			"i"
		);
		const match = source.match(pattern);
		if (match) return normalizeSource(match[1]);
	}

	const genericMatch = source.match(new RegExp(NUMBER_DISPLAY, "i"));
	return genericMatch ? normalizeSource(genericMatch[0]) : "";
}

function findCurrencyNumber(source, label, year) {
	const pattern = currencyPatternForLabel(label);
	if (!pattern) return "";
	const matches = [...source.matchAll(new RegExp(pattern, "gi"))];
	if (!matches.length) return "";
	const withYear = year
		? matches.find(match => {
			const suffix = source.slice(match.index + match[0].length, match.index + match[0].length + 60);
			return new RegExp(`\\b${escapeRegExp(year)}\\w*\\b`).test(suffix);
		})
		: null;
	return normalizeSource((withYear || matches[0])[0]);
}

function currencyPatternForLabel(label) {
	const normalized = String(label || "").trim().toUpperCase();
	const amount = String.raw`\s*[+-]?\d[\d,]*(?:\.\d+)?(?:\s*${MAGNITUDE_WORDS})?`;
	if (normalized === "USD") return String.raw`(?:US\$|\$|USD)${amount}`;
	if (normalized === "JPY") return String.raw`(?:¥|JPY)${amount}`;
	if (normalized === "KRW") return String.raw`(?:₩|KRW)${amount}`;
	if (normalized === "EUR") return String.raw`(?:€|EUR)${amount}`;
	if (normalized === "GBP") return String.raw`(?:£|GBP)${amount}`;
	return "";
}

function formatValueDisplay(value, sourceRaw = "", dataType = "") {
	const label = value && value.label ? String(value.label).trim() : "";
	const year = value && value.year ? String(value.year).trim() : "";
	const rawText = value && value.rawText ? normalizeSource(value.rawText) : "";
	const source = normalizeSource(sourceRaw);
	const type = inferredChartType(dataType, label, source);
	const sourceNumber = findNumberWithContext(source, label, year);
	const fallback = formatChartNumber(value && value.value, type);
	const validRawText = isYearOnlyMeasurementText(rawText, value) ? "" : rawText;
	const validSourceNumber = isYearOnlyMeasurementText(sourceNumber, value) ? "" : sourceNumber;
	let numberText = validRawText || validSourceNumber || fallback;
	const yearText = year ? ` (${year})` : "";
	if (
		label.startsWith("%") &&
		Number.isFinite(Number(value && value.value)) &&
		!String(numberText).includes("%")
	) {
		numberText = `${formatChartNumber(value.value, "percentage")}${label.replace(/^%/, "")}`;
	}

	if (label) return `${label}${yearText}: ${numberText}`;
	if (year) return `${year}: ${numberText}`;
	return numberText;
}

function xLabelForPoint(point, index) {
	if (point && point.year) return String(point.year);
	if (point && point.label) return String(point.label);
	return String(index + 1);
}

function previewLabelIndexes(total, width, options = {}) {
	const count = Math.max(0, Number(total) || 0);
	if (!count) return [];
	const chartWidth = Math.max(0, Number(width) || 0);
	const requestedMax = Number(options.maxVisible);
	const maxVisible = Number.isFinite(requestedMax) && requestedMax > 0
		? Math.min(count, Math.floor(requestedMax))
		: Math.min(count, chartWidth < 220 ? 3 : chartWidth < 300 ? 4 : 6);
	if (count <= maxVisible) {
		return Array.from({ length: count }, (_item, index) => index);
	}
	if (maxVisible <= 1) return [0];
	if (maxVisible === 2) return [0, count - 1];

	const indexes = new Set([0, count - 1]);
	const slots = maxVisible - 1;
	for (let slot = 1; slot < slots; slot += 1) {
		indexes.add(Math.round((slot * (count - 1)) / slots));
	}
	return [...indexes].sort((a, b) => a - b).slice(0, maxVisible);
}

function shouldShowPreviewLabel(index, total, width, options = {}) {
	return previewLabelIndexes(total, width, options).includes(index);
}

const MAGNITUDE_SCALES = [
	{ pattern: /\b(?:quadrillion|Q)\b/i, divisor: 1e15 },
	{ pattern: /\b(?:trillion|T)\b/i, divisor: 1e12 },
	{ pattern: /\b(?:billion|B)\b/i, divisor: 1e9 },
	{ pattern: /\b(?:million|M)\b/i, divisor: 1e6 },
	{ pattern: /\b(?:thousand|K)\b/i, divisor: 1e3 },
];

function firstDisplayNumber(text) {
	const match = cleanChartText(text).match(/[+-]?\d[\d,]*(?:\.\d+)?/);
	if (!match) return null;
	const number = Number(match[0].replace(/,/g, ""));
	return Number.isFinite(number) ? number : null;
}

function inferredMagnitudeDivisor(point) {
	const text = [
		point?.display,
		point?.rawText,
		point?.raw,
		point?.unit,
		point?.label,
	]
		.filter(Boolean)
		.join(" ");
	if (/%|percent/i.test(text)) return 1;
	const match = MAGNITUDE_SCALES.find(scale => scale.pattern.test(text));
	return match ? match.divisor : 1;
}

function valuesNearlyEqual(left, right) {
	const a = Number(left);
	const b = Number(right);
	if (!Number.isFinite(a) || !Number.isFinite(b)) return false;
	const tolerance = Math.max(1e-9, Math.abs(b) * 0.015);
	return Math.abs(a - b) <= tolerance;
}

function normalizedBaseValue(point) {
	const rawValue = Number(point?.value);
	if (!Number.isFinite(rawValue)) return rawValue;
	const divisor = inferredMagnitudeDivisor(point);
	if (divisor <= 1) return rawValue;
	const displayNumber = firstDisplayNumber(
		point?.display || point?.rawText || point?.raw || ""
	);
	if (displayNumber === null) return rawValue;
	const scaledDisplayValue = displayNumber * divisor;
	if (valuesNearlyEqual(rawValue, scaledDisplayValue)) return rawValue;
	if (valuesNearlyEqual(rawValue, displayNumber)) return scaledDisplayValue;
	if (Math.abs(rawValue) < divisor / 10 && Math.abs(displayNumber) < divisor / 10) {
		return scaledDisplayValue;
	}
	return rawValue;
}

function commonPreviewDivisor(values, type = "") {
	if (normalizedChartType(type) === "percentage") return 1;
	const maxAbs = Math.max(
		0,
		...(values || []).map(value => Math.abs(Number(value))).filter(Number.isFinite)
	);
	if (maxAbs >= 1e12) return 1e9;
	if (maxAbs >= 1e9) return 1e9;
	if (maxAbs >= 1e6) return 1e6;
	if (maxAbs >= 1e3) return 1e3;
	return 1;
}

function formatUnitlessPreviewValue(value) {
	const number = Number(value);
	if (!Number.isFinite(number)) return "-";
	const abs = Math.abs(number);
	const digits = abs >= 1000 ? 0 : abs >= 10 ? 1 : abs >= 1 ? 2 : 3;
	return trimFixed(number, digits);
}

function normalizePreviewChartItems(items = [], type = "") {
	const source = Array.isArray(items) ? items : [];
	const baseValues = source.map(normalizedBaseValue);
	const divisor = commonPreviewDivisor(baseValues, type);
	return source.map((item, index) => {
		const baseValue = baseValues[index];
		const value = Number.isFinite(baseValue) ? baseValue / divisor : baseValue;
		return {
			...item,
			value,
			normalizedBaseValue: baseValue,
			previewDivisor: divisor,
			display: formatUnitlessPreviewValue(value),
			unitlessDisplay: formatUnitlessPreviewValue(value),
			stripPreviewUnit: true,
		};
	});
}

module.exports = {
	formatValueDisplay,
	formatChartNumber,
	formatAxisNumber,
	barChartDomain,
	categoryLabelForPoint,
	compactMiddleText,
	displayTextForPoint,
	pieLegendLabelForPoint,
	normalizePreviewChartItems,
	shortValueText,
	xLabelForPoint,
	previewLabelIndexes,
	shouldShowPreviewLabel,
};
