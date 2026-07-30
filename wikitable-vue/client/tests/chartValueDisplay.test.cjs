const assert = require("assert");

const {
	formatValueDisplay,
	formatChartNumber,
	formatAxisNumber,
	barChartDomain,
	canonicalBaseChartItems,
	categoryLabelForPoint,
	compactMiddleText,
	pieLegendLabelForPoint,
	normalizePreviewChartItems,
	matchingValueDisplayToken,
	shortValueText,
	xLabelForPoint,
} = require("../src/js/chartValueDisplay.js");

assert.strictEqual(
	matchingValueDisplayToken(
		239694000000000,
		"¥239,694 billion 43.4% of GDP (2022)",
		"Numerical"
	),
	"¥239,694 billion"
);

assert.strictEqual(
	matchingValueDisplayToken(
		43.4,
		"¥239,694 billion 43.4% of GDP (2022)",
		"Proportional"
	),
	"43.4%"
);

assert.strictEqual(
	matchingValueDisplayToken(
		10,
		"A 10 B 20",
		"Numerical"
	),
	"10",
	"A separated single-letter category must not be attached as a magnitude abbreviation"
);

assert.deepStrictEqual(
	canonicalBaseChartItems(
		normalizePreviewChartItems(
			[
				{ value: 10, label: "A", display: "10", raw: "A 10 B 20" },
				{ value: 20, label: "B", display: "20", raw: "A 10 B 20" },
			],
			"Numerical"
		)
	).map(item => item.value),
	[10, 20],
	"Category labels and unrelated raw text must not supply a magnitude divisor"
);

assert.deepStrictEqual(
	canonicalBaseChartItems(
		normalizePreviewChartItems(
			[{ value: 1.2, display: "1.2B" }],
			"Numerical"
		)
	).map(item => item.value),
	[1200000000],
	"A compact abbreviation directly attached to its measurement number remains supported"
);

assert.strictEqual(
	matchingValueDisplayToken(
		7.4,
		"Sales totaled 7.4 market share 30.2%.",
		"Numerical"
	),
	"7.4"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 1870000000000, year: 2025, label: "nominal" },
		"$1.87 trillion (nominal; 2025) $3.36 trillion (PPP; 2025)",
		"Numerical"
	),
	"nominal (2025): $1.87 trillion"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 22.5, year: 2025, label: "China" },
		"China 22.5% United States 11.6% Japan 7.8% Taiwan 5.1% (2025)",
		"Proportional"
	),
	"China (2025): 22.5%"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 10.5, label: "Machinery" },
		"Electrical machinery 17.6% Mineral fuels 16.6% Machinery 10.5%",
		"Proportional"
	),
	"Machinery: 10.5%"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: -3.5, year: 2020, label: "% of GDP" },
		"-3.5% of GDP (2020)",
		"Proportional"
	),
	"% of GDP (2020): -3.5% of GDP"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 13, label: "nominal" },
		"13th (nominal); 14th (PPP)",
		"Ordinal"
	),
	"nominal: 13th"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 14, label: "PPP" },
		"13th (nominal); 14th (PPP)",
		"Ordinal"
	),
	"PPP: 14th"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 2810, year: 2024, label: "USD" },
		"₩3,835,828 (monthly, 2024) $2,810 (monthly, 2024)",
		"Numerical"
	),
	"USD (2024): $2,810"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 2421, year: 2024, label: "USD" },
		"¥352,541 (monthly, 2024) $2,421 (monthly, 2024)",
		"Numerical"
	),
	"USD (2024): $2,421"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 344700000000, year: 2017, label: "Abroad" },
		"$230.6 billion (31 December 2017 est.) Abroad: $344.7 billion (31 December 2017 est.)",
		"Numerical"
	),
	"Abroad (2017): $344.7 billion"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 814900000000, year: 2024, label: "Exports 2024", rawText: "2024" },
		"exports: $814.9 billion (2024 est.)",
		"Numerical"
	),
	"Exports 2024 (2024): $814.9 billion"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 8.2, year: 2024, label: "Real GDP growth rate 2024", rawText: "2024" },
		"",
		"Trend"
	),
	"Real GDP growth rate 2024 (2024): 8.2%"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 9800, year: 2021, label: "Real GDP per capita 2021", rawText: "2022" },
		"",
		"Numerical"
	),
	"Real GDP per capita 2021 (2021): 9.8K"
);

assert.strictEqual(
	shortValueText(
		{
			value: 814900000000,
			year: 2024,
			display: "Exports 2024 (2024): 2024",
		},
		""
	),
	"814.9B"
);

assert.strictEqual(
	shortValueText(
		{
			value: 6.5,
			year: 2024,
			display: "Real GDP growth rate 2024 (2024): 2024",
		},
		"Percentage"
	),
	"6.5%"
);

assert.strictEqual(
	shortValueText(
		{
			value: 6.5,
			year: 2024,
			display: "Real GDP growth rate 2024 (2024): 6.5",
		},
		"Percentage"
	),
	"6.5%"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 0.929, year: 2023, label: "index", rawText: "0.929 very high (2023)" },
		"0.929 very high (2023) (19th)",
		"Ordinal"
	),
	"index (2023): 0.929 very high (2023)"
);

assert.strictEqual(
	formatValueDisplay(
		{ value: 19, year: 2023, label: "rank", rawText: "19th" },
		"0.929 very high (2023) (19th)",
		"Ordinal"
	),
	"rank (2023): 19th"
);

assert.strictEqual(formatChartNumber(4540000000000), "4.54T");
assert.strictEqual(formatChartNumber(39.8, "percentage"), "39.8%");
assert.strictEqual(formatChartNumber(6.5, "Percentage"), "6.5%");
assert.strictEqual(formatChartNumber(6.5, "Proportional"), "6.5%");
assert.strictEqual(formatChartNumber(2, "percentage"), "2.0%");
assert.deepStrictEqual(
	[10.2, 10.4, 10.6].map(value => formatAxisNumber(value, { min: 10, max: 11 })),
	["10.2", "10.4", "10.6"]
);
assert.deepStrictEqual(
	[0.78, 0.8, 0.82].map(value => formatAxisNumber(value, { min: 0.76, max: 0.84 })),
	["0.78", "0.80", "0.82"]
);
assert.deepStrictEqual(
	[0, 0.005, 0.01, 0.015, 0.02].map(value =>
		formatAxisNumber(value, { min: 0, max: 0.02, splitNumber: 4 })
	),
	["0.000", "0.005", "0.010", "0.015", "0.020"]
);
assert.deepStrictEqual(
	[0, 0.005, 0.01, 0.015, 0.02].map(value =>
		formatAxisNumber(value, {
			min: 0,
			max: 0.02,
			tickValues: [0, 0.005, 0.01, 0.015, 0.02]
		})
	),
	["0.000", "0.005", "0.010", "0.015", "0.020"]
);
assert.strictEqual(formatAxisNumber(39.84, { min: 38, max: 41, type: "percentage" }), "39.8%");
assert.strictEqual(formatAxisNumber(4540000000000, { min: 0, max: 5000000000000 }), "4.54T");
assert.deepStrictEqual(
	normalizePreviewChartItems(
		[
			{ value: 1870000000000, display: "$1.87 trillion" },
			{ value: 814900000000, display: "$814.9 billion" },
		],
		"number"
	).map(item => ({ value: item.value, display: item.display })),
	[
		{ value: 1870, display: "1870" },
		{ value: 814.9, display: "814.9" },
	],
	"Preview chart items should share one magnitude scale and hide units"
);
assert.deepStrictEqual(
	normalizePreviewChartItems(
		[
			{ value: 1.87, display: "$1.87 trillion" },
			{ value: 814.9, display: "$814.9 billion" },
		],
		"number"
	).map(item => ({ value: item.value, display: item.display })),
	[
		{ value: 1870, display: "1870" },
		{ value: 814.9, display: "814.9" },
	],
	"Preview chart normalization should handle values that were extracted in display units"
);
const onceNormalizedTrillionValues = normalizePreviewChartItems(
	[
		{ value: 3913000000000, display: "$3.913 trillion" },
		{ value: 1396000000000, display: "$1.396 trillion" },
	],
	"number"
);
const twiceNormalizedTrillionValues = normalizePreviewChartItems(
	onceNormalizedTrillionValues,
	"number"
);
assert.deepStrictEqual(
	twiceNormalizedTrillionValues.map(item => ({
		value: item.value,
		display: item.display,
		previewDivisor: item.previewDivisor,
	})),
	onceNormalizedTrillionValues.map(item => ({
		value: item.value,
		display: item.display,
		previewDivisor: item.previewDivisor,
	})),
	"Preview chart normalization must be idempotent so pre-normalized table values stay aligned with their shared y-domain"
);

const assertSplitNormalizationPreservesSharedScale = (items, expectedValues, message) => {
	const jointlyNormalized = normalizePreviewChartItems(items, "number");
	assert.deepStrictEqual(
		jointlyNormalized.map(item => item.value),
		expectedValues,
		`${message}: joint normalization should establish the expected shared drawing scale`
	);
	jointlyNormalized.forEach((item, index) => {
		const [sideNormalized] = normalizePreviewChartItems([item], "number");
		assert.strictEqual(
			sideNormalized.previewDivisor,
			item.previewDivisor,
			`${message}: side ${index} must retain the shared preview divisor`
		);
		assert.strictEqual(
			sideNormalized.value,
			item.value,
			`${message}: side ${index} drawing value must stay aligned with scaleContext`
		);
		assert.strictEqual(
			sideNormalized.normalizedBaseValue,
			item.normalizedBaseValue,
			`${message}: side ${index} must retain its original numeric base value`
		);
		assert.strictEqual(
			sideNormalized.originalDisplay,
			items[index].display,
			`${message}: side ${index} must retain its original display text`
		);
	});
};

assertSplitNormalizationPreservesSharedScale(
	[
		{ value: 999, display: "$999" },
		{ value: 1000, display: "$1,000" },
	],
	[0.999, 1],
	"999/1000 cross-side split regression"
);
assertSplitNormalizationPreservesSharedScale(
	[
		{ value: 1000000, display: "$1 million" },
		{ value: 1000000000, display: "$1 billion" },
	],
	[0.001, 1],
	"1e6/1e9 cross-side split regression"
);

const canonicalFullMagnitudeItems = canonicalBaseChartItems(
	normalizePreviewChartItems(
		[
			{ value: 1.87, display: "$1.87 trillion" },
			{ value: 814.9, display: "$814.9 billion" },
		],
		"number"
	)
);
assert.deepStrictEqual(
	canonicalFullMagnitudeItems.map(item => ({
		value: item.value,
		originalValue: item.originalValue,
		display: item.display,
		valueSpace: item.valueSpace,
	})),
	[
		{
			value: 1870000000000,
			originalValue: 1870000000000,
			display: "$1.87 trillion",
			valueSpace: "normalized-base",
		},
		{
			value: 814900000000,
			originalValue: 814900000000,
			display: "$814.9 billion",
			valueSpace: "normalized-base",
		},
	],
	"Full-chart points must draw in the same normalized-base value space as their scale context while retaining original display text"
);

const negativeCurrencyMagnitudeItems = normalizePreviewChartItems(
	[
		{ value: -1.87, display: "-$1.87 trillion" },
		{ value: -1.87, display: "$-1.87 trillion" },
	],
	"number"
);
assert.deepStrictEqual(
	negativeCurrencyMagnitudeItems.map(item => item.normalizedBaseValue),
	[-1870000000000, -1870000000000],
	"Magnitude normalization must preserve a negative sign on either side of the currency symbol"
);
assert.deepStrictEqual(
	canonicalBaseChartItems(negativeCurrencyMagnitudeItems).map(item => ({
		value: item.value,
		originalValue: item.originalValue,
	})),
	[
		{ value: -1870000000000, originalValue: -1870000000000 },
		{ value: -1870000000000, originalValue: -1870000000000 },
	],
	"Canonical full-chart points must retain negative currency magnitude values"
);

const prefixedMagnitudeItems = normalizePreviewChartItems(
	[
		{ value: 814.9, display: "2024: $814.9 billion" },
		{ value: -1.87, display: "GDP 2024: -$1.87 trillion" },
	],
	"number"
);
assert.deepStrictEqual(
	prefixedMagnitudeItems.map(item => item.normalizedBaseValue),
	[814900000000, -1870000000000],
	"Magnitude normalization must match the numeric subject instead of multiplying a year prefix"
);
assert.deepStrictEqual(
	canonicalBaseChartItems(prefixedMagnitudeItems).map(item => ({
		value: item.value,
		originalValue: item.originalValue,
		display: item.display,
	})),
	[
		{
			value: 814900000000,
			originalValue: 814900000000,
			display: "2024: $814.9 billion",
		},
		{
			value: -1870000000000,
			originalValue: -1870000000000,
			display: "GDP 2024: -$1.87 trillion",
		},
	],
	"Canonical full-chart points must retain matched prefixed magnitude values and signs"
);

const closestPrefixedMagnitudeItems = normalizePreviewChartItems(
	[
		{ value: 2000, display: "2024: $2,000 billion" },
		{ value: 10.1, display: "Top 10: $10.1 billion" },
		{ value: 2.01, display: "Q2 2024: $2.01 billion" },
	],
	"number"
);
assert.deepStrictEqual(
	closestPrefixedMagnitudeItems.map(item => Math.round(item.normalizedBaseValue)),
	[2000000000000, 10100000000, 2010000000],
	"Magnitude normalization must choose the closest matching numeric token instead of the first token within tolerance"
);
assert.deepStrictEqual(
	canonicalBaseChartItems(closestPrefixedMagnitudeItems)
		.map(item => Math.round(item.value)),
	[2000000000000, 10100000000, 2010000000],
	"Canonical full-chart values must retain the closest matched magnitude token"
);

const [trustedMetadataItem] = normalizePreviewChartItems(
	[{ value: 1000, display: "$1 thousand" }],
	"number"
);
const [dirtyMetadataItem] = normalizePreviewChartItems(
	[{ ...trustedMetadataItem, value: 1.01 }],
	"number"
);
assert.deepStrictEqual(
	{
		value: dirtyMetadataItem.value,
		normalizedBaseValue: dirtyMetadataItem.normalizedBaseValue,
		previewDivisor: dirtyMetadataItem.previewDivisor,
		originalDisplay: dirtyMetadataItem.originalDisplay,
	},
	{
		value: 1.01,
		normalizedBaseValue: 1.01,
		previewDivisor: 1,
		originalDisplay: "1.01",
	},
	"Dirty preview metadata must discard stale original display text as well as stale numeric metadata"
);

const [percentageFromNumberMetadata] = normalizePreviewChartItems(
	[trustedMetadataItem],
	"percentage"
);
assert.deepStrictEqual(
	{
		value: percentageFromNumberMetadata.value,
		normalizedBaseValue: percentageFromNumberMetadata.normalizedBaseValue,
		previewDivisor: percentageFromNumberMetadata.previewDivisor,
	},
	{ value: 1000, normalizedBaseValue: 1000, previewDivisor: 1 },
	"Percentage normalization must reject reusable non-unit preview divisors"
);

const canonicalMagnitudeItems = normalizePreviewChartItems(
	[
		{ value: 1.87, display: "$1.87 trillion" },
		{ value: 814.9, display: "$814.9 billion" },
	],
	"number"
);
assert.deepStrictEqual(
	canonicalMagnitudeItems.map(item => item.normalizedBaseValue),
	[1870000000000, 814900000000],
	"Canonical full-chart values must reconstruct trillion and billion displays into one base-value space"
);
assert.deepStrictEqual(
	normalizePreviewChartItems(
		[
			{ value: 39.8, display: "39.8%" },
			{ value: 11.6, display: "11.6%" },
		],
		"percentage"
	).map(item => item.display),
	["39.8", "11.6"],
	"Preview chart percentage labels should omit percent signs after units are unified"
);
assert.deepStrictEqual(barChartDomain([-3.5]), [-3.85, 3.85]);
assert.deepStrictEqual(barChartDomain([-3.5, -1.37]), [-3.85, 3.85]);
assert.strictEqual(xLabelForPoint({ year: 2026 }, 0), "2026");
assert.strictEqual(xLabelForPoint({ label: "PPP" }, 1), "PPP");
assert.strictEqual(
	categoryLabelForPoint(
		{ year: 2023, display: "2023: $542.4 billion" },
		0,
		{ fallback: "Gross external debt", total: 1 }
	),
	"2023"
);
assert.strictEqual(
	categoryLabelForPoint(
		{ label: "2023: $542.4 billion", year: 2023, display: "2023: $542.4 billion" },
		0,
		{ fallback: "Gross external debt", total: 1 }
	),
	"2023"
);
assert.strictEqual(
	categoryLabelForPoint({ value: 542400000000, display: "$542.4 billion" }, 0, {
		fallback: "Gross external debt",
		total: 1,
	}),
	"Gross external debt"
);
assert.strictEqual(
	categoryLabelForPoint({ label: "Machinery", display: "Machinery: 10.5%" }, 0),
	"Machinery"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "0-14 years", value: 25.2 }, 0),
	"0-14 years"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "15-64 years", value: 67.1 }, 1),
	"15-64 years"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "years", raw: "0-14 years: 25.2%", value: 25.2 }, 0),
	"0-14 years"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "years and over", raw: "65 years and over: 6.7%", value: 6.7 }, 2),
	"65 years and over"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "years", value: 25.2 }, 0, {
		fallback: "Age structure",
		total: 3,
	}),
	"0-14 years"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "years", value: 25.2 }, 1, {
		fallback: "Age structure",
		total: 4,
	}),
	"0-14 years"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "years", value: 67.1 }, 1, {
		fallback: "Age structure",
		total: 3,
	}),
	"15-64 years"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "years and over", value: 6.7 }, 2, {
		fallback: "Age structure",
		total: 3,
	}),
	"65 years and over"
);
assert.strictEqual(
	pieLegendLabelForPoint({ label: "% of GDP", year: 2024, value: 2.8 }, 0),
	"2024"
);
assert.strictEqual(
	pieLegendLabelForPoint({ raw: "Machinery: 10.5%", value: 10.5 }, 0),
	"Machinery"
);
assert.strictEqual(
	pieLegendLabelForPoint(
		{ label: "Women married by age 15", display: "Women married by age 15: 1.2%" },
		0
	),
	"Women married by age 15"
);
assert.notStrictEqual(
	compactMiddleText("Women married by age 15", 16),
	compactMiddleText("Women married by age 18", 16)
);
assert(
	compactMiddleText("Women married by age 15", 16).includes("15"),
	"middle ellipsis should preserve the distinguishing suffix"
);

console.log("chartValueDisplay tests passed");
