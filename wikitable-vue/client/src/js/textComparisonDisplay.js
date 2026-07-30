const { formatValueDisplay } = require("./chartValueDisplay.js");

function buildTextPairs(row) {
	const leftItems = textItems(row, "left");
	const rightItems = textItems(row, "right");
	const rightUsed = new Set();
	const pairs = [];

	leftItems.forEach((leftItem, leftIndex) => {
		const rightIndex = findMatchingTextItem(leftItem, rightItems, rightUsed, leftIndex);
		const rightItem = rightIndex >= 0 ? rightItems[rightIndex] : emptyTextItem();
		if (rightIndex >= 0) rightUsed.add(rightIndex);
		pairs.push(makeTextPair(pairs.length + 1, leftItem, rightItem));
	});

	rightItems.forEach((rightItem, rightIndex) => {
		if (!rightUsed.has(rightIndex)) {
			pairs.push(makeTextPair(pairs.length + 1, emptyTextItem(), rightItem));
		}
	});

	if (
		pairs.length === 1 &&
		!pairs[0].left.displayLabel &&
		!pairs[0].right.displayLabel
	) {
		pairs[0].left.markerText = "";
		pairs[0].left.showIndex = false;
		pairs[0].right.markerText = "";
		pairs[0].right.showIndex = false;
	}

	return pairs.length ? pairs : [makeTextPair(1, emptyTextItem(), emptyTextItem())];
}

function textItems(row, side) {
	const sideData = (row.visualization && row.visualization[side]) || {};
	const rawItems = splitTextValue(sideData.raw);
	if (Array.isArray(sideData.values) && sideData.values.length) {
		return sideData.values.map((value, index) =>
			textItemFromValue(value, sideData.raw, row.dataType, index, rawItems[index])
		);
	}
	return rawItems.map((item, index) => ({
		...item,
		key: normalizeTextKey(item.label || item.value),
		order: index,
	}));
}

function textItemFromValue(value, sourceRaw, dataType, index, rawItem = null) {
	const explicitLabel = (value && (value.label || value.year)) || "";
	const label = cleanPairLabel(explicitLabel || (rawItem && rawItem.label) || "");
	const display = explicitLabel || !(rawItem && rawItem.value)
		? formatValueDisplay(value, sourceRaw, dataType)
		: rawItem.value;
	return {
		label,
		value: stripDisplayLabel(display, label),
		key: normalizeTextKey(label || display),
		order: index,
	};
}

function splitTextValue(raw) {
	const text = cleanTextValue(String(raw || "").replace(/\u00a0/g, " "));
	if (!text || text === "-") return [];
	const ordinalItems = splitOrdinalParentheticalSeries(text);
	if (ordinalItems.length >= 2) return ordinalItems.slice(0, 5);
	const agencyItems = splitCreditRatingSections(text);
	if (agencyItems.length >= 2) return agencyItems.slice(0, 5);
	const parts = splitTopLevelTextParts(text);

	return parts
		.map(part => textItemFromRawPart(part))
		.filter(item => item.value)
		.slice(0, 5);
}

function splitTopLevelTextParts(text) {
	const parts = [];
	let start = 0;
	let depth = 0;
	for (let index = 0; index < text.length; index += 1) {
		const char = text[index];
		if (char === "(") depth += 1;
		if (char === ")" && depth > 0) depth -= 1;
		if (depth === 0 && isTopLevelSeparator(text, index)) {
			parts.push(text.slice(start, index));
			start = index + 1;
		}
	}
	if (parts.length) {
		parts.push(text.slice(start));
		return parts;
	}
	return splitShortCommaList(text);
}

function isTopLevelSeparator(text, index) {
	const char = text[index];
	if (char === ";" || char === "•" || char === "·" || char === "|" || char === "\n") {
		return true;
	}
	if (char !== "-") return false;
	return /\s/.test(text[index - 1] || "") && /\s/.test(text[index + 1] || "");
}

function splitOrdinalParentheticalSeries(text) {
	const matches = [...text.matchAll(/(\d+)(st|nd|rd|th)\s*\((.*?)(?=(?:\)\s*)?\d+(?:st|nd|rd|th)\s*\(|$)/gi)];
	return matches
		.map(match => {
			const label = labelFromParentheticalContext(match[3]);
			return {
				label,
				value: `${match[1]}${match[2]}`,
			};
		})
		.filter(item => item.label && item.value);
}

function splitCreditRatingSections(text) {
	const sectionPattern = /(Standard\s*&\s*Poor's|Moody's|Fitch):/gi;
	const matches = [...text.matchAll(sectionPattern)];
	if (matches.length < 2) return [];
	return matches.map((match, index) => {
		const nextMatch = matches[index + 1];
		return {
			label: cleanPairLabel(match[1].replace(/\s+/g, " ")),
			value: cleanTextValue(text.slice(match.index + match[0].length, nextMatch ? nextMatch.index : text.length)),
		};
	}).filter(item => item.label && item.value);
}

function splitShortCommaList(text) {
	const commaParts = splitTopLevelCommas(text).map(cleanTextValue).filter(Boolean);
	if (
		commaParts.length >= 2 &&
		commaParts.length <= 5 &&
		text.length <= 120 &&
		!/[.!?]/.test(text) &&
		!/\b(?:and|or|with|including)\b/i.test(text)
	) {
		return commaParts;
	}
	return [text];
}

function splitTopLevelCommas(text) {
	const parts = [];
	let start = 0;
	let depth = 0;
	for (let index = 0; index < text.length; index += 1) {
		const char = text[index];
		if (char === "(") depth += 1;
		if (char === ")" && depth > 0) depth -= 1;
		if (char === "," && depth === 0) {
			parts.push(text.slice(start, index));
			start = index + 1;
		}
	}
	if (!parts.length) return [text];
	parts.push(text.slice(start));
	return parts;
}

function textItemFromRawPart(rawPart) {
	const part = cleanTextValue(rawPart);
	const prefixMatch = part.match(/^([A-Za-z][A-Za-z /&-]{1,32}):\s*(.+)$/);
	if (prefixMatch) {
		const label = cleanPairLabel(prefixMatch[1]);
		if (label) {
			return {
				label,
				value: cleanTextValue(prefixMatch[2]),
			};
		}
	}

	const parentheticalMatch = part.match(/^(.+?)\s*\(([^)]*)\)\s*$/);
	if (parentheticalMatch) {
		const label = labelFromParentheticalContext(parentheticalMatch[2]);
		if (label) {
			return {
				label,
				value: cleanTextValue(parentheticalMatch[1]),
			};
		}
	}

	return {
		label: "",
		value: part,
	};
}

function labelFromParentheticalContext(context) {
	const withoutYear = String(context || "")
		.replace(/\b(?:18|19|20|21)\d{2}\w*\b/g, "")
		.replace(/\b(?:est|estimate|estimated|forecast|f|proj|projected)\b/gi, "")
		.replace(/[()]/g, "");
	const label = cleanPairLabel(withoutYear.split(/[;,/]/).find(part => cleanPairLabel(part)) || "");
	return label;
}

function stripDisplayLabel(display, label) {
	const text = cleanTextValue(display);
	if (!label) return text;
	const escaped = escapeRegExp(label);
	const pattern = new RegExp(`^${escaped}(?:\\s*\\([^)]*\\))?\\s*:\\s*`, "i");
	return cleanTextValue(text.replace(pattern, ""));
}

function cleanTextValue(value) {
	return String(value || "")
		.replace(/^\s*[-–—•·]\s*/, "")
		.replace(/\s+/g, " ")
		.trim();
}

function cleanPairLabel(value) {
	const label = cleanTextValue(value);
	if (!label || /^\d+$/.test(label)) return "";
	if (/\b(?:18|19|20|21)\d{2}\b/.test(label)) return "";
	if (/\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b/i.test(label)) return "";
	const normalized = label.toLowerCase() === "ppp" ? "PPP" : label;
	return normalized.length > 28 ? `${normalized.slice(0, 27)}...` : normalized;
}

function normalizeTextKey(value) {
	return String(value || "")
		.toLowerCase()
		.replace(/[^a-z0-9\u4e00-\u9fa5]+/g, " ")
		.trim();
}

function emptyTextItem() {
	return {
		label: "",
		value: "",
		key: "",
		order: -1,
	};
}

function findMatchingTextItem(leftItem, rightItems, rightUsed, fallbackIndex) {
	if (leftItem.key) {
		const exactIndex = rightItems.findIndex(
			(item, index) => !rightUsed.has(index) && item.key && item.key === leftItem.key
		);
		if (exactIndex >= 0) return exactIndex;
	}
	return !rightUsed.has(fallbackIndex) && rightItems[fallbackIndex] ? fallbackIndex : -1;
}

function makeTextPair(index, leftItem, rightItem) {
	const labels = displayLabels(leftItem.label, rightItem.label);
	return {
		index,
		left: {
			...leftItem,
			displayLabel: labels.left,
			markerText: labels.left || String(index),
			showIndex: !labels.left,
		},
		right: {
			...rightItem,
			displayLabel: labels.right,
			markerText: labels.right || String(index),
			showIndex: !labels.right,
		},
	};
}

function displayLabels(leftLabel, rightLabel) {
	const left = cleanPairLabel(leftLabel);
	const right = cleanPairLabel(rightLabel);
	if (left && right && normalizeTextKey(left) === normalizeTextKey(right)) {
		return { left, right: left };
	}
	if (left && right) return { left, right };
	if (left) return { left, right: left };
	if (right) return { left: right, right };
	return { left: "", right: "" };
}

function escapeRegExp(value) {
	return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

module.exports = {
	buildTextPairs,
	textItems,
	textItemFromRawPart,
	stripDisplayLabel,
};
