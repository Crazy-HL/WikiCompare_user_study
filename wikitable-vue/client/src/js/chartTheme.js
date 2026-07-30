const CHART_COLORS = Object.freeze([
	"#3498db",
	"#e74c3c",
	"#2ecc71",
	"#f39c12",
	"#9b59b6",
]);

const CHART_REMAINDER_COLOR = "#f0f0f0";
const CHART_LINE_WIDTH = 2;

const FALLBACK_CATEGORY_COLORS = Object.freeze([
	"#4e79a7",
	"#f28e2b",
	"#e15759",
	"#76b7b2",
	"#59a14f",
	"#edc949",
	"#af7aa1",
	"#ff9da7",
	"#9c755f",
	"#bab0ab",
]);

const CATEGORY_COLORS = Object.freeze({
	Machinery: "#8dd3c7",
	"Mineral Fuels": "#ffffb3",
	"Integrated Circuits": "#bebada",
	"Vehicles and their parts": "#fb8072",
	Plastics: "#80b1d3",
	"Iron and Steel": "#fdb462",
	"Instruments and Apparatus": "#b3de69",
	"Organic Chemicals": "#fccde5",
	"Transport Equipment": "#bc80bd",
	"Electrical Machinery": "#ccebc5",
	Chemicals: "#ffed6f",
	"Manufactured Goods": "#d9d9d9",
	"Raw Materials": "#fdb462",
	Foodstuff: "#ffb347",
	Others: "#a9a9a9",
	Electronics: "#fdb462",
	telecommunications: "#b3de69",
	"automobile production": "#fccde5",
	shipbuilding: "#d9d9d9",
	steel: "#bc80bd",
	"High technology": "#ccebc5",
	"Motor vehicles": "#ffed6f",
	"Machine tools": "#8dd3c7",
	China: "#fb8072",
	"United States": "#80b1d3",
	ASEAN: "#fdb462",
	"European Union": "#b3de69",
	Taiwan: "#fccde5",
	Japan: "#d9d9d9",
	"South Korea": "#bc80bd",
});

const normalizeCategoryKey = value =>
	String(value || "")
		.replace(/[.:\s]*$/, "")
		.replace(/\s+/g, " ")
		.trim()
		.toLowerCase();

const colorFromMap = (map, name) => {
	if (!map || !name) return null;
	if (map[name]) return map[name];
	const normalizedName = normalizeCategoryKey(name);
	const matchedKey = Object.keys(map).find(
		key => normalizeCategoryKey(key) === normalizedName
	);
	return matchedKey ? map[matchedKey] : null;
};

const chartColor = index => CHART_COLORS[index % CHART_COLORS.length];

const categoryColor = (name, index = 0, overrides = {}) =>
	colorFromMap(overrides, name) ||
	colorFromMap(CATEGORY_COLORS, name) ||
	FALLBACK_CATEGORY_COLORS[index % FALLBACK_CATEGORY_COLORS.length];

module.exports = {
	CHART_COLORS,
	CHART_REMAINDER_COLOR,
	CHART_LINE_WIDTH,
	CATEGORY_COLORS,
	FALLBACK_CATEGORY_COLORS,
	chartColor,
	categoryColor,
};
