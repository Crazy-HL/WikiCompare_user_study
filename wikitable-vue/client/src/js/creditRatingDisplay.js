const AGENCY_ALIASES = {
	"standard & poor's": { agency: "S&P", fullAgency: "Standard & Poor's" },
	"moody's": { agency: "Moody's", fullAgency: "Moody's" },
	fitch: { agency: "Fitch", fullAgency: "Fitch" },
};

const AGENCY_ORDER = ["S&P", "Moody's", "Fitch"];

function isCreditRatingRow(row) {
	return String(row?.label || "").trim().toLowerCase() === "credit rating";
}

function buildCreditRatingPairs(row) {
	const left = parseCreditRatingText(row?.visualization?.left?.raw);
	const right = parseCreditRatingText(row?.visualization?.right?.raw);
	const leftByAgency = new Map(left.map(item => [item.agency, item]));
	const rightByAgency = new Map(right.map(item => [item.agency, item]));
	const agencyNames = [
		...AGENCY_ORDER,
		...left.map(item => item.agency),
		...right.map(item => item.agency),
	].filter((agency, index, agencies) => agency && agencies.indexOf(agency) === index);

	return agencyNames
		.map(agency => ({
			agency,
			left: leftByAgency.get(agency) || emptyAgency(agency),
			right: rightByAgency.get(agency) || emptyAgency(agency),
		}))
		.filter(pair => pair.left.items.length || pair.right.items.length);
}

function parseCreditRatingText(raw) {
	const text = cleanText(raw);
	if (!text) return [];
	const agencyPattern = /(Standard\s*&\s*Poor's|Moody's|Fitch):/gi;
	const matches = [...text.matchAll(agencyPattern)];
	if (!matches.length) return [];

	return matches
		.map((match, index) => {
			const agencyMeta = agencyAlias(match[1]);
			const nextMatch = matches[index + 1];
			const section = cleanText(text.slice(match.index + match[0].length, nextMatch ? nextMatch.index : text.length));
			return {
				agency: agencyMeta.agency,
				fullAgency: agencyMeta.fullAgency,
				items: parseAgencyItems(section),
			};
		})
		.filter(section => section.items.length);
}

function parseAgencyItems(section) {
	const text = cleanText(section);
	if (!text) return [];
	const items = [];
	const ratingPattern = /([A-Za-z]{1,3}[+-]?\d?|A{1,3}[+-]?)\s*\((Domestic|Foreign|T&C Assessment)\)/gi;
	let lastEnd = 0;
	let match;
	while ((match = ratingPattern.exec(text)) !== null) {
		items.push({
			label: normalizeRatingLabel(match[2]),
			value: match[1],
		});
		lastEnd = match.index + match[0].length;
	}

	const outlookMatch = text.match(/\bOutlook:\s*([A-Za-z ]+?)(?=$|\s+[A-Z][a-z]+:)/i);
	const remainder = cleanText(text.slice(lastEnd).replace(/\bOutlook:\s*[A-Za-z ]+/i, ""));
	if (!items.length && remainder) {
		items.push({ label: "Rating", value: remainder });
	}
	if (outlookMatch) {
		items.push({ label: "Outlook", value: cleanText(outlookMatch[1]) });
	}
	return items;
}

function normalizeRatingLabel(label) {
	const clean = cleanText(label);
	if (/^T&C/i.test(clean)) return "T&C";
	return clean;
}

function agencyAlias(value) {
	const key = cleanText(value).toLowerCase();
	return AGENCY_ALIASES[key] || { agency: cleanText(value), fullAgency: cleanText(value) };
}

function emptyAgency(agency) {
	return {
		agency,
		fullAgency: agency,
		items: [],
	};
}

function cleanText(value) {
	return String(value || "").replace(/\s+/g, " ").trim();
}

module.exports = {
	buildCreditRatingPairs,
	isCreditRatingRow,
	parseAgencyItems,
	parseCreditRatingText,
};
