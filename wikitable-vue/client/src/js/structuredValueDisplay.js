function hasStructuredValues(row) {
	return ["left", "right"].some(side => {
		const values = row?.visualization?.[side]?.structuredValues;
		return Array.isArray(values) && values.length > 0;
	});
}

function buildStructuredListItems(row, side) {
	const currentValues = normalizeValues(row?.visualization?.[side]?.structuredValues);
	const otherSide = side === "left" ? "right" : "left";
	const otherKeys = new Set(
		normalizeValues(row?.visualization?.[otherSide]?.structuredValues)
			.map(item => normalizedKey(item.value || item.label))
	);
	return currentValues.map(item => ({
		...item,
		display: displayText(item),
		hasDistinctLabel: hasDistinctLabel(item),
		shared: otherKeys.has(normalizedKey(item.value || item.label)),
	}));
}

function normalizeValues(values) {
	if (!Array.isArray(values)) return [];
	const seen = new Set();
	const items = [];
	values.forEach(value => {
		const text = cleanText(value?.value || value?.label);
		if (!text) return;
		const key = normalizedKey(text);
		if (seen.has(key)) return;
		seen.add(key);
		items.push({
			label: cleanText(value?.label) || text,
			value: text,
			kind: cleanText(value?.kind) || "item",
		});
	});
	return items;
}

function normalizedKey(value) {
	return cleanText(value).toLowerCase();
}

function displayText(item) {
	const label = cleanText(item?.label);
	const value = cleanText(item?.value);
	if (!label || label === value) return value || label;
	return `${label}: ${value}`;
}

function hasDistinctLabel(item) {
	const label = cleanText(item?.label);
	const value = cleanText(item?.value);
	return Boolean(label && value && normalizedKey(label) !== normalizedKey(value));
}

function cleanText(value) {
	return String(value || "").replace(/\s+/g, " ").trim();
}

module.exports = {
	buildStructuredListItems,
	hasStructuredValues,
};
