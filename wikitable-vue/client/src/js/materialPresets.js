const MATERIAL_PRESETS = Object.freeze([
	{
		id: "economy-korea-japan",
		label: "South Korea vs Japan",
		type: "高相似结构",
		domain: "economy",
		description: "South Korea 和 Japan 的经济页面结构相近，包含 GDP data、infobox 与正文经济数据，适合作为稳定基准材料。",
		left: {
			title: "Economy of South Korea",
			pageTitle: "Economy_of_South_Korea",
			revision: "1273871505",
		},
		right: {
			title: "Economy of Japan",
			pageTitle: "Economy_of_Japan",
			revision: "1297943898",
		},
	},
	{
		id: "openfactbook-india-indonesia",
		label: "India vs Indonesia OpenFactBook profile (2026)",
		type: "真实网页多指标国家画像",
		domain: "development",
		description: "OpenFactBook 国家画像页面包含 population、birth rate、death rate、health expenditure、religions、ethnic groups 等大量字段型正文数据，适合展示 10+ 个可视化对比属性与多种图表类型。",
		left: {
			title: "India OpenFactBook profile (2026)",
			url: "https://openfactbook.org/countries/india/",
		},
		right: {
			title: "Indonesia OpenFactBook profile (2026)",
			url: "https://openfactbook.org/countries/indonesia/",
		},
	},
]);

const materialUrl = article =>
	article.url ||
	`https://en.wikipedia.org/w/index.php?title=${article.pageTitle}&oldid=${article.revision}`;

module.exports = {
	MATERIAL_PRESETS,
	materialUrl,
};
