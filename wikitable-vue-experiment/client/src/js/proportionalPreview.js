function buildCompactProportionalRows(values, options = {}) {
	return buildCompactValueRows(values, options);
}

function buildCompactValueRows(values, options = {}) {
	const limit = Number.isFinite(Number(options.limit)) ? Number(options.limit) : 5;
	const items = Array.isArray(values) ? values : [];
	const rows = items
		.map((item, index) => {
			const value = Number(item?.value);
			const display = cleanText(item?.display || item?.raw || "");
			return {
				label: compactLabel(item?.label || item?.raw || display || `Item ${index + 1}`, display),
				value,
				valueText: valueText(item?.display, value),
				index,
				isMore: false,
			};
		})
		.filter(row => row.label && Number.isFinite(row.value))

	const visible = rows.slice(0, limit);
	const hiddenCount = Math.max(0, rows.length - visible.length);
	if (hiddenCount) {
		visible.push({
			label: `+ ${hiddenCount} more`,
			value: null,
			valueText: "",
			index: rows.length,
			isMore: true,
		});
	}
	return visible;
}

function cleanLabel(value) {
	return cleanText(value).replace(/:$/, "");
}

function compactLabel(label, display) {
	const clean = cleanLabel(label);
	const displayText = cleanText(display);
	if (displayText && clean === displayText) {
		const parts = splitDisplay(displayText);
		if (parts) return cleanLabel(parts.label);
	}
	return clean;
}

function cleanText(value) {
	return String(value || "").replace(/\s+/g, " ").trim();
}

function valueText(display, value) {
	const text = cleanText(display);
	if (!text) return formatPercent(value);
	const parts = splitDisplay(text);
	if (parts?.value) return parts.value;
	return text;
}

function splitDisplay(text) {
	const colonIndex = text.lastIndexOf(":");
	if (colonIndex < 0) return null;
	const label = cleanText(text.slice(0, colonIndex));
	const value = cleanText(text.slice(colonIndex + 1));
	if (!label || !value) return null;
	return { label, value };
}

function formatPercent(value) {
	const number = Number(value);
	if (!Number.isFinite(number)) return "";
	return `${number.toFixed(2).replace(/\.?0+$/, "")}%`;
}

module.exports = {
	buildCompactProportionalRows,
	buildCompactValueRows,
};
