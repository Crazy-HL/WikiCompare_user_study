const MAGNITUDE_WORDS =
	"(?:quadrillion|trillion|billion|million|thousand|percent)";
const NUMBER_DISPLAY = String.raw`(?:US\$|[$¥₩€£])?\s*[+-]?\d[\d,]*(?:\.\d+)?\s*(?:${MAGNITUDE_WORDS}|%)?`;

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

function formatChartNumber(value, type = "") {
	const num = Number(value);
	if (!Number.isFinite(num)) return "-";
	if (type === "percentage") return `${num.toFixed(1)}%`;

	const abs = Math.abs(num);
	if (abs >= 1e12) return `${trimFixed(num / 1e12)}T`;
	if (abs >= 1e9) return `${trimFixed(num / 1e9)}B`;
	if (abs >= 1e6) return `${trimFixed(num / 1e6)}M`;
	if (abs >= 1e3) return `${trimFixed(num / 1e3)}K`;
	return trimFixed(num, Math.abs(num) < 10 ? 1 : 0);
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
		"i"
	);
	const categoryMatch = source.match(categoryPattern);
	if (categoryMatch) return normalizeSource(categoryMatch[1]);

	const labelIndex = source.toLowerCase().indexOf(String(label).toLowerCase());
	if (labelIndex >= 0) {
		const before = source.slice(Math.max(0, labelIndex - 80), labelIndex);
		const after = source.slice(labelIndex, labelIndex + 80);
		const beforeMatches = [...before.matchAll(new RegExp(NUMBER_DISPLAY, "gi"))];
		if (beforeMatches.length) {
			return normalizeSource(beforeMatches[beforeMatches.length - 1][0]);
		}
		const afterMatch = after.match(new RegExp(NUMBER_DISPLAY, "i"));
		if (afterMatch) return normalizeSource(afterMatch[0]);
	}
	return "";
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

function formatValueDisplay(value, sourceRaw = "", dataType = "") {
	const label = value && value.label ? String(value.label).trim() : "";
	const year = value && value.year ? String(value.year).trim() : "";
	const source = normalizeSource(sourceRaw);
	const type = String(dataType || "").toLowerCase() === "proportional"
		? "percentage"
		: "";
	const sourceNumber = findNumberWithContext(source, label, year);
	const fallback = formatChartNumber(value && value.value, type);
	let numberText = sourceNumber || fallback;
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

module.exports = {
	formatValueDisplay,
	formatChartNumber,
	barChartDomain,
	xLabelForPoint,
};
