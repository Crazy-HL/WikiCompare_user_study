const MATERIAL_PRESETS = Object.freeze([
	{
		id: "economy-korea-japan",
		label: "South Korea vs Japan",
		type: "高相似结构",
		domain: "economy",
		description: "标准经济类 infobox 与正文结构化比较，适合作为练习或主实验材料。",
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
		id: "retail-amazon-walmart",
		label: "Amazon vs Walmart",
		type: "零售与平台公司",
		domain: "retail",
		description: "零售与平台公司对比，正文和 infobox 都包含 revenue、employees、marketplace scale 与 business data。",
		left: {
			title: "Amazon",
			pageTitle: "Amazon_(company)",
			revision: "1362240360",
		},
		right: {
			title: "Walmart",
			pageTitle: "Walmart",
			revision: "1362721520",
		},
	},
	{
		id: "health-covid-italy-spain",
		label: "COVID-19: Italy vs Spain",
		type: "公共卫生事件",
		domain: "health",
		description: "公共卫生事件材料包含 cases、deaths、hospitalized cases、recovered data 与百分比变化，正文数据丰富。",
		left: {
			title: "COVID-19 pandemic in Italy",
			pageTitle: "COVID-19_pandemic_in_Italy",
			revision: "1358452073",
		},
		right: {
			title: "COVID-19 pandemic in Spain",
			pageTitle: "COVID-19_pandemic_in_Spain",
			revision: "1354735558",
		},
	},
	{
		id: "energy-solar-china-us",
		label: "Solar power: China vs United States",
		type: "能源基础设施",
		domain: "energy",
		description: "能源文章正文中常见 installed capacity、generation percentage、policy targets 等可视化数据。",
		left: {
			title: "Solar power in China",
			pageTitle: "Solar_power_in_China",
			revision: "1361511699",
		},
		right: {
			title: "Solar power in the United States",
			pageTitle: "Solar_power_in_the_United_States",
			revision: "1361214159",
		},
	},
	{
		id: "demographics-india-china",
		label: "Demographics: India vs China",
		type: "人口结构",
		domain: "demographics",
		description: "人口文章强调 population、age structure、growth percentage 与 demographic indicators，适合正文数据抽取。",
		left: {
			title: "Demographics of India",
			pageTitle: "Demographics_of_India",
			revision: "1361189624",
		},
		right: {
			title: "Demographics of China",
			pageTitle: "Demographics_of_China",
			revision: "1362115664",
		},
	},
]);

const materialUrl = article =>
	`https://en.wikipedia.org/w/index.php?title=${article.pageTitle}&oldid=${article.revision}`;

module.exports = {
	MATERIAL_PRESETS,
	materialUrl,
};
