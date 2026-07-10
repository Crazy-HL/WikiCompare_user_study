const { formatValueDisplay } = require("./chartValueDisplay.js");

function buildComparisonDisplayPlan(row) {
	const leftItems = sideItems(row, "left");
	const rightItems = sideItems(row, "right");
	if (!leftItems.length && rightItems.length) leftItems.push(emptyDisplayItem());
	if (!rightItems.length && leftItems.length) rightItems.push(emptyDisplayItem());

	if (isSingleValueRow(leftItems, rightItems)) {
		return {
			left: leftItems.map(item => singleDisplayItem(item)),
			right: rightItems.map(item => singleDisplayItem(item)),
		};
	}

	applyPositionalLabelsWhenUnlabeled(leftItems, rightItems);
	assignLabelOccurrences(leftItems, rightItems);

	const sharedSlots = sharedDisplaySlots(leftItems, rightItems);
	const sharedIndexBySlot = new Map(sharedSlots.map((slot, index) => [slot, index]));

	return {
		left: plannedSideItems(leftItems, "left", sharedIndexBySlot),
		right: plannedSideItems(rightItems, "right", sharedIndexBySlot),
	};
}

function normalizeDisplayLabel(label) {
	return cleanText(label)
		.toLowerCase()
		.replace(/[^\p{L}\p{N}]+/gu, " ")
		.trim();
}

function sideItems(row, side) {
	const sideData = row?.visualization?.[side] || {};
	const values = Array.isArray(sideData.values) ? sideData.values : [];
	const structuredValues = Array.isArray(sideData.structuredValues)
		? sideData.structuredValues
		: [];
	const useFormattedValues = values.length > 0;
	const displayValues = useFormattedValues ? values : structuredValues;
	if (!displayValues.length) {
		const raw = cleanText(sideData.raw);
		return raw ? [normalizedItem({ display: raw }, 0)] : [];
	}
	return displayValues
		.map((value, index) =>
			normalizedItem(value, index, {
				dataType: row?.dataType,
				sourceRaw: sideData.raw,
				useFormattedValues,
			})
		)
		.filter(item => item.valueText || item.label);
}

function normalizedItem(value, index, options = {}) {
	const sourceLabel = cleanText(firstPresent(value?.label, value?.year));
	let label = sourceLabel;
	const rawFallback = firstPresent(value?.value, value?.raw);
	const formattedDisplay = options.useFormattedValues
		? formatValueDisplay(value, options.sourceRaw, options.dataType)
		: "";
	const fallbackDisplay =
		formattedDisplay && formattedDisplay !== "-" ? formattedDisplay : rawFallback;
	const displayText = cleanText(firstPresent(value?.display, fallbackDisplay));
	if (
		!options.useFormattedValues &&
		normalizeDisplayLabel(label) &&
		normalizeDisplayLabel(label) === normalizeDisplayLabel(displayText)
	) {
		label = "";
	}
	return {
		label,
		normalizedLabel: normalizeDisplayLabel(sourceLabel || label),
		valueText: stripDisplayPrefix(displayText, label),
		order: index,
	};
}

function emptyDisplayItem() {
	return {
		label: "",
		normalizedLabel: "",
		valueText: "—",
		order: 0,
	};
}

function isSingleValueRow(leftItems, rightItems) {
	return leftItems.length <= 1 && rightItems.length <= 1;
}

function singleDisplayItem(item) {
	return {
		label: "",
		valueText: item?.valueText ?? "",
		shared: false,
		colorKey: "single",
		key: "single",
	};
}

function applyPositionalLabelsWhenUnlabeled(leftItems, rightItems) {
	if (!allItemsUnlabeled(leftItems) || !allItemsUnlabeled(rightItems)) return;
	[leftItems, rightItems].forEach(items => {
		items.forEach((item, index) => {
			item.label = String(index + 1);
			item.normalizedLabel = normalizeDisplayLabel(item.label);
		});
	});
}

function assignLabelOccurrences(leftItems, rightItems) {
	const leftCounts = countLabels(leftItems);
	const rightCounts = countLabels(rightItems);
	[leftItems, rightItems].forEach(items => {
		const seen = new Map();
		items.forEach(item => {
			if (!item.normalizedLabel) {
				item.labelOccurrence = item.order;
				item.hasDuplicateLabel = false;
				return;
			}
			const occurrence = seen.get(item.normalizedLabel) || 0;
			seen.set(item.normalizedLabel, occurrence + 1);
			item.labelOccurrence = occurrence;
			item.hasDuplicateLabel =
				Math.max(
					leftCounts.get(item.normalizedLabel) || 0,
					rightCounts.get(item.normalizedLabel) || 0
				) > 1;
		});
	});
}

function countLabels(items) {
	const counts = new Map();
	items.forEach(item => {
		if (!item.normalizedLabel) return;
		counts.set(item.normalizedLabel, (counts.get(item.normalizedLabel) || 0) + 1);
	});
	return counts;
}

function allItemsUnlabeled(items) {
	return items.length > 1 && items.every(item => !item.normalizedLabel);
}

function sharedDisplaySlots(leftItems, rightItems) {
	const rightSlots = new Set(rightItems.map(item => itemSlotKey(item)).filter(Boolean));
	const seen = new Set();
	return leftItems
		.map(item => itemSlotKey(item))
		.filter(slot => {
			if (!slot || !rightSlots.has(slot) || seen.has(slot)) return false;
			seen.add(slot);
			return true;
		});
}

function plannedSideItems(items, side, sharedIndexBySlot) {
	let unmatchedIndex = 0;
	return [...items]
		.sort((first, second) => sortDisplayItems(first, second, sharedIndexBySlot))
		.map(item => {
			const sharedIndex = sharedIndexBySlot.get(itemSlotKey(item));
			if (sharedIndex !== undefined) {
				return displayItem(item, true, `shared-${sharedIndex}`, sharedOutputKey(item));
			}
			const colorKey = `unmatched-${side}-${unmatchedIndex}`;
			unmatchedIndex += 1;
			return displayItem(item, false, colorKey, unmatchedOutputKey(item, side));
		});
}

function sortDisplayItems(first, second, sharedIndexBySlot) {
	const firstSharedIndex = sharedIndexBySlot.get(itemSlotKey(first));
	const secondSharedIndex = sharedIndexBySlot.get(itemSlotKey(second));
	if (firstSharedIndex !== undefined && secondSharedIndex !== undefined) {
		return firstSharedIndex - secondSharedIndex;
	}
	if (firstSharedIndex !== undefined) return -1;
	if (secondSharedIndex !== undefined) return 1;
	return first.order - second.order;
}

function displayItem(item, shared, colorKey, key) {
	return {
		label: item.label,
		valueText: item.valueText,
		shared,
		colorKey,
		key,
	};
}

function itemSlotKey(item) {
	if (!item.normalizedLabel) return "";
	return `${item.normalizedLabel}:${item.labelOccurrence || 0}`;
}

function sharedOutputKey(item) {
	if (!item.hasDuplicateLabel) return `shared-${item.normalizedLabel}`;
	return `shared-${item.normalizedLabel}-${item.labelOccurrence || 0}`;
}

function unmatchedOutputKey(item, side) {
	if (!item.normalizedLabel) return `${side}-${item.order}`;
	if (!item.hasDuplicateLabel) return `${side}-${item.normalizedLabel}`;
	return `${side}-${item.normalizedLabel}-${item.labelOccurrence || 0}`;
}

function stripDisplayPrefix(displayText, label) {
	const text = cleanText(displayText);
	const cleanLabel = cleanText(label);
	if (!text || !cleanLabel) return text;
	const escapedLabel = cleanLabel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const prefixPattern = new RegExp(`^${escapedLabel}(?:\\s*\\([^)]*\\))?\\s*:\\s*`, "i");
	return text.replace(prefixPattern, "");
}

function firstPresent(...values) {
	return values.find(value => value !== null && value !== undefined && value !== "");
}

function cleanText(value) {
	if (value === null || value === undefined) return "";
	return String(value).replace(/\s+/g, " ").trim();
}

module.exports = {
	buildComparisonDisplayPlan,
	normalizeDisplayLabel,
};
