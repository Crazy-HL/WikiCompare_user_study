const {
	barChartDomain,
	formatChartNumber,
	formatValueDisplay,
	xLabelForPoint,
} = require("./chartValueDisplay");

const SIDE_KEYS = ["left", "right"];

function buildMergedComparison(row, articleTitles = {}) {
	const sides = SIDE_KEYS.map(side => normalizeSide(row, side, articleTitles[side]));
	const allPoints = sides.flatMap(side => side.points);
	const categories = mergedCategories(sides, row);
	const mode = chooseMode(row, sides, categories);
	const series = sides.map(side => ({
		name: side.title,
		side: side.key,
		raw: side.raw,
		data: categories.map(category => {
			const point = bestPointForCategory(side.points, category, mode);
			return point
				? {
						value: point.value,
						display: point.display,
						raw: point.raw,
						label: point.label,
						year: point.year,
				  }
				: { value: null, display: "-", raw: "", label: category };
		}),
	}));
	const numericValues = series
		.flatMap(item => item.data.map(point => point.value))
		.filter(Number.isFinite);

	return {
		title: row?.label || "Comparison",
		mode,
		unit: inferUnit(row, allPoints),
		categories,
		series,
		yDomain: numericValues.length ? barChartDomain(numericValues) : [0, 1],
		stats: buildStats(sides, numericValues, row),
		rawDetails: sides.map(side => ({ label: side.title, value: side.raw || "-" })),
	};
}

function normalizeSide(row, side, title) {
	const sideData = row?.visualization?.[side] || {};
	const raw = sideData.raw === null || sideData.raw === undefined
		? ""
		: String(sideData.raw);
	const values = Array.isArray(sideData.values) ? sideData.values : [];
	const fallbackPoints = raw
		? [{ value: null, label: row?.label || side, raw, display: raw }]
		: [];
	const points = (values.length ? values : fallbackPoints).map((value, index) => {
		const point = typeof value === "object" && value !== null
			? value
			: { value, raw: String(value) };
		const label = point.label || (point.year ? String(point.year) : row?.label || `Item ${index + 1}`);
		const numericValue = toFiniteNumber(point.value);
		return {
			...point,
			value: numericValue,
			label: String(label),
			category: point.year ? String(point.year) : String(label),
			year: point.year,
			raw: point.raw || raw,
			display: point.display || displayForPoint(point, raw, row?.dataType),
		};
	});

	return {
		key: side,
		title: title || side,
		raw,
		points,
	};
}

function displayForPoint(point, raw, dataType) {
	if (
		point?.label &&
		String(point.label).startsWith("%") &&
		Number.isFinite(Number(point.value))
	) {
		return `${formatChartNumber(point.value, "percentage")}${String(point.label).replace(/^%/, "")}`;
	}
	const display = formatValueDisplay(point, raw, dataType);
	if (display && display !== "-") {
		const prefixes = [
			point?.label ? `${point.label}: ` : "",
			point?.year ? `${point.year}: ` : "",
			point?.year ? `${point.year} ` : "",
		].filter(Boolean);
		const matchedPrefix = prefixes.find(prefix => String(display).startsWith(prefix));
		return matchedPrefix ? String(display).slice(matchedPrefix.length) : display;
	}
	if (point?.raw) return String(point.raw);
	return formatChartNumber(point?.value, unitType(dataType));
}

function mergedCategories(sides, row) {
	const labels = sides.flatMap(side => side.points.map(point => point.category));
	const unique = [...new Set(labels.filter(Boolean))];
	if (!unique.length) return [row?.label || "Value"];
	const allYears = unique.every(category => /^\d{4}$/.test(String(category)));
	if (allYears) return unique.sort((a, b) => Number(a) - Number(b));
	if (unique.length === 1) return [row?.label || unique[0]];
	return unique.sort((a, b) => String(a).localeCompare(String(b)));
}

function chooseMode(row, sides, categories) {
	const mergeVisualization = String(row?.mergeVisualization || "").toLowerCase();
	if (mergeVisualization === "bar-chart") return "bar";
	if (mergeVisualization === "stacked-chart") return "bar";
	if (mergeVisualization === "pie-chart") return "bar";
	if (mergeVisualization === "text-only") return "text";

	const hasYearSeries = sides.every(side =>
		side.points.filter(point => point.year && Number.isFinite(point.value)).length >= 2
	);
	if (mergeVisualization === "line-chart" && hasYearSeries && categories.length >= 2) return "line";
	const numericCount = sides.flatMap(side => side.points).filter(point => Number.isFinite(point.value)).length;
	if (numericCount <= 2 && categories.length <= 1) return "single";
	if (numericCount > 0) return "bar";
	return "text";
}

function bestPointForCategory(points, category, mode) {
	if (mode === "single") {
		return points.find(point => Number.isFinite(point.value)) || points[0];
	}
	return points.find(point => point.category === category || point.label === category);
}

function buildStats(sides, numericValues, row) {
	const leftValue = firstNumericValue(sides[0]);
	const rightValue = firstNumericValue(sides[1]);
	const delta = Number.isFinite(leftValue) && Number.isFinite(rightValue)
		? Math.abs(leftValue - rightValue)
		: null;
	const type = unitType(row?.dataType);

	return {
		leftDisplay: firstDisplayValue(sides[0]),
		rightDisplay: firstDisplayValue(sides[1]),
		delta,
		deltaDisplay: delta === null ? "-" : formatChartNumber(delta, type),
		maxDisplay: numericValues.length
			? formatChartNumber(Math.max(...numericValues), type)
			: "-",
	};
}

function inferUnit(row, points) {
	const raw = [
		row?.visualization?.left?.raw,
		row?.visualization?.right?.raw,
		...points.map(point => point.raw),
	]
		.filter(Boolean)
		.join(" ");
	const dataType = String(row?.dataType || "").toLowerCase();
	const isProportional = dataType === "proportional";
	if (!isProportional && /US\$|\$/.test(raw)) return "USD";
	if (!isProportional && /¥/.test(raw)) return "JPY";
	if (!isProportional && /₩/.test(raw)) return "KRW";
	if (/%\s*of\s*GDP/i.test(raw)) return "% of GDP";
	if (/%/.test(raw) || isProportional) return "%";
	if (/US\$|\$/.test(raw)) return "USD";
	if (/¥/.test(raw)) return "JPY";
	if (/₩/.test(raw)) return "KRW";
	return "";
}

function unitType(dataType) {
	return String(dataType || "").toLowerCase() === "proportional"
		? "percentage"
		: "";
}

function firstNumericValue(side) {
	const point = side?.points?.find(item => Number.isFinite(item.value));
	return point ? point.value : null;
}

function firstDisplayValue(side) {
	const point = side?.points?.find(item => item.display);
	return point?.display || "-";
}

function toFiniteNumber(value) {
	const number = Number(value);
	return Number.isFinite(number) ? number : null;
}

module.exports = {
	buildMergedComparison,
	normalizeSide,
	xLabelForPoint,
};
