const assert = require("assert");

const {
	formatValueDisplay,
	formatChartNumber,
	barChartDomain,
	xLabelForPoint,
} = require("../src/js/chartValueDisplay.js");

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
		{ value: -3.5, year: 2020, label: "% of GDP" },
		"-3.5% of GDP (2020)",
		"Proportional"
	),
	"% of GDP (2020): -3.5% of GDP"
);

assert.strictEqual(formatChartNumber(4540000000000), "4.54T");
assert.strictEqual(formatChartNumber(39.8, "percentage"), "39.8%");
assert.strictEqual(formatChartNumber(2, "percentage"), "2.0%");
assert.deepStrictEqual(barChartDomain([-3.5]), [-3.85, 3.85]);
assert.deepStrictEqual(barChartDomain([-3.5, -1.37]), [-3.85, 3.85]);
assert.strictEqual(xLabelForPoint({ year: 2026 }, 0), "2026");
assert.strictEqual(xLabelForPoint({ label: "PPP" }, 1), "PPP");

console.log("chartValueDisplay tests passed");
