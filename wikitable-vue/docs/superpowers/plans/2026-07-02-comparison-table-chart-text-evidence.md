# Comparison Table Chart Text Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make WikiCompare's comparison table, URL controls, chart modals, main-text extraction, and source highlighting coherent, simple, and comparison-first.

**Architecture:** Add one shared client-side display-plan utility for aligned `label: value` table rendering, then reuse that logic in table cells and text chart modals. Keep backend row normalization as the source of primary/related source IDs so hover highlighting can include both infobox and body text evidence. Keep chart components ECharts-based, but simplify modal chrome and preserve chart families.

**Tech Stack:** Vue 3 single-file components, CommonJS utility modules in `client/src/js`, ECharts, Tornado Python backend, pytest, Node assertion tests.

---

## File Structure

- Create `client/src/js/comparisonDisplayPlan.js`
  - Builds left/right aligned display lines with shared label ordering and color tokens.
  - Shared by table cells and text-only chart/modal rendering.

- Create `client/tests/comparisonDisplayPlan.test.cjs`
  - Tests label ordering, shared colors, single-value behavior, and unmatched labels.

- Modify `client/src/components/compoents_base/CompareTable.vue`
  - Replace mixed table preview branches for comparable values with the shared display-plan renderer.
  - Use combined primary + related source IDs for hover.
  - Keep credit-rating special rendering only if it is clearer than generic display.

- Modify `client/src/components/compoents_base/SimpleChart.vue`
  - Stop rendering mini SVG charts for multi-value table cells.
  - Render the shared display-plan `label: value` list for all table-side multi-value rows.

- Modify `client/src/components/UrlCompareForm.vue`
  - Polish collapsed and expanded URL controls.

- Modify `client/src/js/mergedComparisonData.js`
  - Preserve merged chart mode based on source visualization.
  - Preserve category ordering using shared labels first.
  - Support gap/null values for missing categories.

- Modify `client/tests/mergedComparisonData.test.cjs`
  - Add line-preservation, category ordering, and stacked/pie mode tests.

- Modify `client/src/components/compoents_base/MergedComparisonChart.vue`
  - Remove large summary cards and raw-value cards.
  - Render clean chart with title, legend, axes, tooltip, and restrained labels.

- Modify `client/src/components/compoents_base/FullChart.vue`
  - Use category labels for x-axis when values have labels.
  - Simplify modal chart style and remove duplicated raw detail blocks from the primary visual path.

- Modify `server/services/attribute_pool.py`
  - Deduplicate text attributes against infobox attributes.
  - Add related sentence IDs to infobox-derived attributes when main text repeats or supports them.

- Modify `server/services/llm_client.py`
  - Strengthen text attribute extraction prompt for body-text-first comparable facts.

- Modify `server/server.py`
  - Align text attributes beyond exact lowercase keys.
  - Include related source IDs in ranked rows.

- Modify `server/services/pipeline.py`
  - Preserve `leftRelatedSourceIds` and `rightRelatedSourceIds` in normalized rows.

- Modify `server/tests/test_attribute_pool.py`
  - Test text deduplication and related evidence merging.

- Modify `server/tests/test_compare_api.py`
  - Test compare-session response includes text-derived attributes and related source IDs.

- Modify `server/tests/test_pipeline.py`
  - Test normalized rows carry related source IDs.

- Modify `client/src/components/compoents_base/ParentComponent.vue`
  - Add softer related-source highlight class while keeping existing primary highlight behavior.

- Modify `client/src/js/sessionStore.js`
  - Track primary and related highlight IDs separately if needed by `ParentComponent.vue`.

---

## Task 1: Shared Table Display Plan

**Files:**
- Create: `client/src/js/comparisonDisplayPlan.js`
- Create: `client/tests/comparisonDisplayPlan.test.cjs`

- [ ] **Step 1: Write the failing test**

Create `client/tests/comparisonDisplayPlan.test.cjs`:

```js
const assert = require("assert");

const {
	buildComparisonDisplayPlan,
	normalizeDisplayLabel,
} = require("../src/js/comparisonDisplayPlan.js");

const fdiRow = {
	label: "FDI stock",
	dataType: "Numerical",
	visualization: {
		left: {
			raw: "$230.6 billion (2017) Abroad: $344.7 billion (2017)",
			values: [
				{ label: "Inward", value: 230600000000, year: 2017, display: "Inward (2017): $230.6 billion" },
				{ label: "Abroad", value: 344700000000, year: 2017, display: "Abroad (2017): $344.7 billion" },
			],
		},
		right: {
			raw: "Inward: $25 billion (2021) Outward: $147 billion (2021)",
			values: [
				{ label: "Inward", value: 25000000000, year: 2021, display: "Inward (2021): $25 billion" },
				{ label: "Outward", value: 147000000000, year: 2021, display: "Outward (2021): $147 billion" },
			],
		},
	},
};

const fdiPlan = buildComparisonDisplayPlan(fdiRow);

assert.deepStrictEqual(
	fdiPlan.left.map(item => `${item.label}: ${item.valueText} ${item.shared ? "shared" : "solo"} ${item.colorKey}`),
	[
		"Inward: $230.6 billion shared shared-0",
		"Abroad: $344.7 billion solo unmatched-left-0",
	]
);

assert.deepStrictEqual(
	fdiPlan.right.map(item => `${item.label}: ${item.valueText} ${item.shared ? "shared" : "solo"} ${item.colorKey}`),
	[
		"Inward: $25 billion shared shared-0",
		"Outward: $147 billion solo unmatched-right-0",
	]
);

const singleRow = {
	label: "Population",
	dataType: "Numerical",
	visualization: {
		left: { raw: "51.5 million (2025)", values: [{ value: 51500000, year: 2025, display: "51.5 million" }] },
		right: { raw: "123,262,483 (2025)", values: [{ value: 123262483, year: 2025, display: "123,262,483" }] },
	},
};

const singlePlan = buildComparisonDisplayPlan(singleRow);
assert.deepStrictEqual(singlePlan.left, [
	{ label: "", valueText: "51.5 million", shared: false, colorKey: "single", key: "single" },
]);
assert.deepStrictEqual(singlePlan.right, [
	{ label: "", valueText: "123,262,483", shared: false, colorKey: "single", key: "single" },
]);

const unlabeledMultiRow = {
	label: "Example",
	visualization: {
		left: { raw: "10; 20", values: [{ value: 10, display: "10" }, { value: 20, display: "20" }] },
		right: { raw: "11; 19", values: [{ value: 11, display: "11" }, { value: 19, display: "19" }] },
	},
};
const unlabeledPlan = buildComparisonDisplayPlan(unlabeledMultiRow);
assert.strictEqual(unlabeledPlan.left[0].label, "1");
assert.strictEqual(unlabeledPlan.right[0].label, "1");

assert.strictEqual(normalizeDisplayLabel("  PPP "), "ppp");
assert.strictEqual(normalizeDisplayLabel("United States"), "united states");

console.log("comparisonDisplayPlan tests passed");
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node client/tests/comparisonDisplayPlan.test.cjs
```

Expected: FAIL with `Cannot find module '../src/js/comparisonDisplayPlan.js'`.

- [ ] **Step 3: Implement the display-plan utility**

Create `client/src/js/comparisonDisplayPlan.js`:

```js
function buildComparisonDisplayPlan(row) {
	const leftItems = normalizeSide(row, "left");
	const rightItems = normalizeSide(row, "right");
	const leftHasLabels = leftItems.some(item => item.key);
	const rightHasLabels = rightItems.some(item => item.key);
	const bothUnlabeledMulti =
		leftItems.length > 1 &&
		rightItems.length > 1 &&
		!leftHasLabels &&
		!rightHasLabels;

	const preparedLeft = leftItems.map((item, index) =>
		prepareItem(item, index, bothUnlabeledMulti)
	);
	const preparedRight = rightItems.map((item, index) =>
		prepareItem(item, index, bothUnlabeledMulti)
	);

	if (preparedLeft.length === 1 && preparedRight.length === 1) {
		return {
			left: [singleValueItem(preparedLeft[0])],
			right: [singleValueItem(preparedRight[0])],
		};
	}

	const sharedKeys = preparedLeft
		.map(item => item.key)
		.filter(key => key && preparedRight.some(right => right.key === key));
	const orderedSharedKeys = [...new Set(sharedKeys)];

	return {
		left: orderItems(preparedLeft, orderedSharedKeys, "left"),
		right: orderItems(preparedRight, orderedSharedKeys, "right"),
	};
}

function normalizeSide(row, side) {
	const sideData = row?.visualization?.[side] || {};
	const values = Array.isArray(sideData.values) ? sideData.values : [];
	if (values.length) {
		return values.map((value, index) => {
			const label = cleanText(value?.label || "");
			const display = cleanValueText(value?.display || value?.rawText || value?.raw || value?.value);
			return {
				label,
				key: normalizeDisplayLabel(label),
				valueText: stripDisplayPrefix(display, label),
				index,
			};
		});
	}
	const raw = cleanValueText(sideData.raw);
	return raw ? [{ label: "", key: "", valueText: raw, index: 0 }] : [];
}

function prepareItem(item, index, bothUnlabeledMulti) {
	if (!item.key && bothUnlabeledMulti) {
		const label = String(index + 1);
		return { ...item, label, key: label };
	}
	return item;
}

function orderItems(items, sharedKeys, side) {
	const shared = sharedKeys
		.map((key, index) => {
			const item = items.find(candidate => candidate.key === key);
			return item ? decorateItem(item, true, `shared-${index}`) : null;
		})
		.filter(Boolean);
	const unmatched = items
		.filter(item => !sharedKeys.includes(item.key))
		.map((item, index) => decorateItem(item, false, `unmatched-${side}-${index}`));
	return [...shared, ...unmatched];
}

function decorateItem(item, shared, colorKey) {
	return {
		label: item.label,
		valueText: item.valueText,
		shared,
		colorKey,
		key: item.key || colorKey,
	};
}

function singleValueItem(item) {
	return {
		label: "",
		valueText: item?.valueText || "-",
		shared: false,
		colorKey: "single",
		key: "single",
	};
}

function stripDisplayPrefix(display, label) {
	const text = cleanValueText(display);
	const cleanLabelText = cleanText(label);
	if (!cleanLabelText) return text;
	const patterns = [
		new RegExp(`^${escapeRegExp(cleanLabelText)}\\s*\\([^)]*\\)\\s*:\\s*`, "i"),
		new RegExp(`^${escapeRegExp(cleanLabelText)}\\s*:\\s*`, "i"),
	];
	return cleanValueText(patterns.reduce((current, pattern) => current.replace(pattern, ""), text));
}

function cleanValueText(value) {
	return cleanText(value).replace(/\s+/g, " ");
}

function cleanText(value) {
	return String(value ?? "").replace(/\u00a0/g, " ").trim();
}

function normalizeDisplayLabel(value) {
	return cleanText(value)
		.toLowerCase()
		.replace(/[^\p{L}\p{N}]+/gu, " ")
		.replace(/\s+/g, " ")
		.trim();
}

function escapeRegExp(value) {
	return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

module.exports = {
	buildComparisonDisplayPlan,
	normalizeDisplayLabel,
};
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node client/tests/comparisonDisplayPlan.test.cjs
```

Expected: `comparisonDisplayPlan tests passed`.

- [ ] **Step 5: Commit**

```bash
git add client/src/js/comparisonDisplayPlan.js client/tests/comparisonDisplayPlan.test.cjs
git commit -m "feat: add aligned comparison display plan"
```

---

## Task 2: Apply Display Plan to the Three-Column Table

**Files:**
- Modify: `client/src/components/compoents_base/CompareTable.vue`
- Modify: `client/src/components/compoents_base/SimpleChart.vue`
- Test: `client/tests/comparisonDisplayPlan.test.cjs`

- [ ] **Step 1: Write the failing test for color-token stability**

Append to `client/tests/comparisonDisplayPlan.test.cjs`:

```js
const reorderedRow = {
	label: "GDP by sector",
	visualization: {
		left: {
			values: [
				{ label: "Agriculture", display: "Agriculture: 1.6%" },
				{ label: "Industry", display: "Industry: 31.6%" },
				{ label: "Services", display: "Services: 58.4%" },
			],
		},
		right: {
			values: [
				{ label: "Services", display: "Services: 71.4%" },
				{ label: "Agriculture", display: "Agriculture: 1.0%" },
				{ label: "Industry", display: "Industry: 26.9%" },
			],
		},
	},
};

const reorderedPlan = buildComparisonDisplayPlan(reorderedRow);
assert.deepStrictEqual(reorderedPlan.left.map(item => item.label), [
	"Agriculture",
	"Industry",
	"Services",
]);
assert.deepStrictEqual(reorderedPlan.right.map(item => item.label), [
	"Agriculture",
	"Industry",
	"Services",
]);
assert.deepStrictEqual(
	reorderedPlan.left.map(item => item.colorKey),
	reorderedPlan.right.map(item => item.colorKey)
);
```

- [ ] **Step 2: Run the test to verify it fails if Task 1 does not already support right reordering**

Run:

```bash
node client/tests/comparisonDisplayPlan.test.cjs
```

Expected: FAIL if right-side shared labels preserve their original order instead of the left shared order. If it passes, continue.

- [ ] **Step 3: Update `CompareTable.vue` imports and helpers**

In `client/src/components/compoents_base/CompareTable.vue`, import:

```js
const { buildComparisonDisplayPlan } = require("@/js/comparisonDisplayPlan");
```

Add helpers:

```js
const displayPlan = row => buildComparisonDisplayPlan(row);
const displayItems = (row, side) => displayPlan(row)[side] || [];
const isSimpleComparableRow = row => {
	const sideHasValues = ["left", "right"].some(side =>
		Array.isArray(row.visualization?.[side]?.values) &&
		row.visualization[side].values.length
	);
	return sideHasValues && !isCreditRatingRow(row) && !hasStructuredValues(row);
};
```

- [ ] **Step 4: Replace value-cell branches for comparable rows**

In both left and right value-cell templates, put this branch before `isTextRow(row)` and before `<SimpleChart>`:

```vue
<div
	v-if="isSimpleComparableRow(row)"
	class="comparison-value-list"
	:class="`comparison-value-list-${side}`">
	<div
		v-for="item in displayItems(row, side)"
		:key="`${side}-${row.id}-${item.key}`"
		class="comparison-value-line"
		:class="[item.colorKey, { 'is-shared': item.shared, 'is-single': !item.label }]">
		<span v-if="item.label" class="comparison-value-label">{{ item.label }}:</span>
		<strong class="comparison-value-text">{{ item.valueText }}</strong>
	</div>
</div>
```

Because the template has separate left and right blocks, use literal `left` and `right` in each branch instead of a dynamic `side` variable.

- [ ] **Step 5: Add table list CSS**

Add scoped CSS:

```css
.comparison-value-list {
	display: grid;
	width: 100%;
	gap: 5px;
	align-content: start;
	justify-items: stretch;
}

.comparison-value-line {
	display: flex;
	align-items: baseline;
	gap: 4px;
	min-height: 24px;
	padding: 4px 6px;
	border: 1px solid #dbe4ef;
	border-radius: 6px;
	background: #ffffff;
	color: #1f2937;
	font-size: 11px;
	line-height: 1.25;
	text-align: left;
}

.comparison-value-line.is-single {
	justify-content: center;
	text-align: center;
	font-weight: 750;
}

.comparison-value-label {
	flex: 0 1 auto;
	min-width: 0;
	color: #475569;
	font-weight: 800;
	overflow-wrap: anywhere;
}

.comparison-value-text {
	flex: 1 1 auto;
	min-width: 0;
	color: #111827;
	font-weight: 800;
	overflow-wrap: anywhere;
}

.comparison-value-line.shared-0 { border-left: 3px solid #3867a8; }
.comparison-value-line.shared-1 { border-left: 3px solid #5f8f3f; }
.comparison-value-line.shared-2 { border-left: 3px solid #d9902f; }
.comparison-value-line.shared-3 { border-left: 3px solid #7d5fb2; }
.comparison-value-line.shared-4 { border-left: 3px solid #2f8c8f; }
.comparison-value-line[class*="unmatched"] { border-left: 3px solid #cbd5e1; }
```

- [ ] **Step 6: Stop `SimpleChart.vue` from acting as table multi-value renderer**

Keep `SimpleChart.vue` available for true single-value mini charts if still used, but after `CompareTable.vue` branches route multi-value rows through `comparison-value-list`, do not add more table rendering logic to `SimpleChart.vue`.

- [ ] **Step 7: Run tests**

Run:

```bash
node client/tests/comparisonDisplayPlan.test.cjs
node client/tests/textComparisonDisplay.test.cjs
node client/tests/proportionalPreview.test.cjs
```

Expected: all pass.

- [ ] **Step 8: Browser check table DOM**

Open `http://127.0.0.1:8080/`, load Korea vs Japan, and run a DOM audit equivalent to:

```js
[...document.querySelectorAll(".comparison-value-list")].length > 0
```

Expected:

- `GDP`, `FDI stock`, `GDP by sector`, `Unemployment`, `GDP rank`, and salary rows use `label: value`.
- Shared labels have matching `shared-*` classes on both sides.
- Single-value rows do not show `Value:`.

- [ ] **Step 9: Commit**

```bash
git add client/src/components/compoents_base/CompareTable.vue client/src/components/compoents_base/SimpleChart.vue client/tests/comparisonDisplayPlan.test.cjs
git commit -m "feat: unify comparison table value rendering"
```

---

## Task 3: Polish URL Controls

**Files:**
- Modify: `client/src/components/UrlCompareForm.vue`

- [ ] **Step 1: Add a structural smoke test by DOM class names**

This project does not currently have a Vue component test runner. Use browser verification for visual behavior and keep this task scoped to component markup/CSS.

- [ ] **Step 2: Update collapsed template copy**

Change the collapsed summary to use a session-strip structure:

```vue
<div class="url-summary">
	<div class="brand-lockup">
		<strong>WikiCompare</strong>
		<span v-if="leftTitle && rightTitle" class="session-pair">
			{{ leftTitle }} <span class="swap-mark">↔</span> {{ rightTitle }}
		</span>
		<span v-else class="session-pair">Ready to compare</span>
	</div>
	<button class="toggle-button" type="button" @click="toggleExpanded">
		{{ isExpanded ? "Collapse" : "Change" }}
	</button>
</div>
```

Add computed values:

```js
const leftTitle = computed(() => store.session?.articles?.left?.title || "");
const rightTitle = computed(() => store.session?.articles?.right?.title || "");
```

- [ ] **Step 3: Update expanded form layout**

Keep the existing form fields and actions, but style them as a restrained control panel:

```css
.url-shell {
	position: relative;
	z-index: 20;
	background: rgba(248, 250, 252, 0.96);
	border-bottom: 1px solid #dbe4ef;
	box-shadow: none;
	backdrop-filter: blur(10px);
}

.url-summary {
	display: flex;
	min-height: 42px;
	align-items: center;
	justify-content: space-between;
	gap: 14px;
	padding: 6px 16px;
}

.brand-lockup {
	display: flex;
	min-width: 0;
	align-items: baseline;
	gap: 14px;
}

.brand-lockup strong {
	color: #0f172a;
	font-size: 15px;
	font-weight: 800;
}

.session-pair {
	min-width: 0;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	color: #64748b;
	font-size: 12px;
	font-weight: 650;
}

.swap-mark {
	color: #3867a8;
	padding: 0 6px;
}

.url-form {
	display: grid;
	grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
	gap: 10px;
	align-items: end;
	padding: 8px 16px 12px;
	border-top: 1px solid #e5eaf1;
}
```

- [ ] **Step 4: Browser verify**

Capture screenshots of:

- collapsed URL strip
- expanded URL panel

Expected:

- collapsed strip is 40-44px tall
- expanded panel does not dominate the viewport
- recent comparisons are compact chips

- [ ] **Step 5: Commit**

```bash
git add client/src/components/UrlCompareForm.vue
git commit -m "style: refine comparison URL controls"
```

---

## Task 4: Preserve Merged Chart Type and Simplify Modal

**Files:**
- Modify: `client/src/js/mergedComparisonData.js`
- Modify: `client/tests/mergedComparisonData.test.cjs`
- Modify: `client/src/components/compoents_base/MergedComparisonChart.vue`

- [ ] **Step 1: Write failing merged-mode tests**

Append to `client/tests/mergedComparisonData.test.cjs`:

```js
const lineRow = {
	label: "GDP growth",
	mergeVisualization: "line-chart",
	dataType: "Trend",
	visualization: {
		left: { values: [{ year: 2024, value: 2.0 }, { year: 2025, value: 1.0 }] },
		right: { values: [{ year: 2024, value: 0.2 }, { year: 2025, value: 0.7 }] },
	},
};

const lineMerged = buildMergedComparison(lineRow, { left: "Korea", right: "Japan" });
assert.strictEqual(lineMerged.mode, "line");
assert.deepStrictEqual(lineMerged.categories, ["2024", "2025"]);

const fdiMerged = buildMergedComparison({
	label: "FDI stock",
	mergeVisualization: "bar-chart",
	dataType: "Numerical",
	visualization: {
		left: { values: [{ label: "Inward", value: 230 }, { label: "Abroad", value: 344 }] },
		right: { values: [{ label: "Inward", value: 25 }, { label: "Outward", value: 147 }] },
	},
});

assert.strictEqual(fdiMerged.mode, "bar");
assert.deepStrictEqual(fdiMerged.categories, ["Inward", "Abroad", "Outward"]);
assert.strictEqual(fdiMerged.series[1].data[1].value, null);

const stackedMerged = buildMergedComparison({
	label: "GDP by sector",
	mergeVisualization: "stacked-chart",
	dataType: "Proportional",
	visualization: {
		left: { values: [{ label: "Agriculture", value: 1.6 }, { label: "Industry", value: 31.6 }] },
		right: { values: [{ label: "Agriculture", value: 1.0 }, { label: "Industry", value: 26.9 }] },
	},
});
assert.strictEqual(stackedMerged.mode, "stacked");
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
node client/tests/mergedComparisonData.test.cjs
```

Expected: FAIL because current `chooseMode()` maps `stacked-chart` to `bar`, and category order may sort alphabetically.

- [ ] **Step 3: Update mode selection**

In `client/src/js/mergedComparisonData.js`, change `chooseMode()`:

```js
if (mergeVisualization === "line-chart" && hasYearSeries && categories.length >= 2) return "line";
if (mergeVisualization === "stacked-chart") return "stacked";
if (mergeVisualization === "pie-chart") return "bar";
if (mergeVisualization === "bar-chart") return "bar";
if (mergeVisualization === "text-only") return "text";
```

- [ ] **Step 4: Update category ordering**

Change `mergedCategories()` to preserve left side order, then right-only labels:

```js
function mergedCategories(sides, row) {
	const leftCategories = sides[0]?.points.map(point => point.category).filter(Boolean) || [];
	const rightCategories = sides[1]?.points.map(point => point.category).filter(Boolean) || [];
	const all = [...leftCategories, ...rightCategories];
	const unique = [...new Set(all)];
	if (!unique.length) return [row?.label || "Value"];
	const allYears = unique.every(category => /^\d{4}$/.test(String(category)));
	if (allYears) return unique.sort((a, b) => Number(a) - Number(b));
	return unique;
}
```

- [ ] **Step 5: Simplify `MergedComparisonChart.vue` template**

Remove `.merged-summary` and `.raw-values` from the template. Keep:

```vue
<div class="merged-comparison">
	<div ref="chartEl" class="merged-chart"></div>
</div>
```

Keep title in the existing modal header from `CompareTable.vue`.

- [ ] **Step 6: Update ECharts option for stacked mode**

In `chartOption(data)`, add:

```js
const isStacked = data.mode === "stacked";
```

For each series:

```js
type: isLine ? "line" : "bar",
stack: isStacked ? "total" : undefined,
```

Keep legend, axes, grid, tooltip. Set labels to:

```js
label: {
	show: !isStacked && data.categories.length <= 4,
	position: pointLabelPosition(data, item),
	color: "#243447",
	fontSize: 10,
	formatter: params => params.data?.display || "-"
}
```

- [ ] **Step 7: Run tests**

Run:

```bash
node client/tests/mergedComparisonData.test.cjs
```

Expected: all pass.

- [ ] **Step 8: Browser verify merged chart**

Check:

- `GDP growth` merged chart is line.
- `FDI stock` merged chart is grouped bar with categories `Inward`, `Abroad`, `Outward`.
- `GDP by sector` merged chart is stacked/proportional style.
- Modal has no large summary cards or raw-value cards.

- [ ] **Step 9: Commit**

```bash
git add client/src/js/mergedComparisonData.js client/tests/mergedComparisonData.test.cjs client/src/components/compoents_base/MergedComparisonChart.vue
git commit -m "feat: preserve merged chart semantics"
```

---

## Task 5: Simplify Enlarged Single Chart

**Files:**
- Modify: `client/src/components/compoents_base/FullChart.vue`
- Modify: `client/src/components/compoents_base/CompareTable.vue`
- Test: browser verification

- [ ] **Step 1: Update x-axis label logic**

In `FullChart.vue`, change bar x-axis data from:

```js
data: data.map((item, index) => xLabelForPoint(item, index)),
```

to:

```js
data: data.map((item, index) => item.label || xLabelForPoint(item, index)),
```

Expected effect: `FDI stock` enlarged chart x-axis shows `Inward`, `Abroad`, not two `2017` labels.

- [ ] **Step 2: Reduce duplicated labels**

In `barOption()`, show direct labels only for small data:

```js
label: {
	show: data.length <= 4,
	position: "top",
	color: "#1f2937",
	fontSize: 10,
	formatter: params => params.data?.shortDisplay || params.data?.display || "-"
}
```

- [ ] **Step 3: Remove bottom details from primary modal**

In `CompareTable.vue`, remove or hide:

```vue
<div v-if="!currentChart.combined && currentChart.details.length" class="chart-details">
```

For this iteration, do not render chart details beneath enlarged charts.

- [ ] **Step 4: Simplify modal chrome**

Keep `.modal-content`, `.chart-container`, and close button, but reduce modal padding and keep chart area dominant:

```css
.modal-content {
	width: min(980px, 92vw);
	max-height: 86vh;
	padding: 16px;
}

.chart-container {
	min-height: 420px;
}
```

- [ ] **Step 5: Browser verify enlarged chart**

Check:

- `FDI stock` left enlarged chart has x-axis `Inward`, `Abroad`.
- No large duplicated raw-value block below chart.
- Tooltip still shows full values.
- Text-only rows still show readable aligned text.

- [ ] **Step 6: Commit**

```bash
git add client/src/components/compoents_base/FullChart.vue client/src/components/compoents_base/CompareTable.vue
git commit -m "style: simplify enlarged chart modal"
```

---

## Task 6: Main-Text Attributes and Related Evidence

**Files:**
- Modify: `server/services/attribute_pool.py`
- Modify: `server/services/llm_client.py`
- Modify: `server/server.py`
- Modify: `server/services/pipeline.py`
- Modify: `server/tests/test_attribute_pool.py`
- Modify: `server/tests/test_compare_api.py`
- Modify: `server/tests/test_pipeline.py`

- [ ] **Step 1: Write failing attribute-pool test**

Append to `server/tests/test_attribute_pool.py`:

```python
def test_build_attribute_pool_merges_duplicate_text_evidence_into_infobox():
    article = {
        "infobox": [
            {"id": "left-info-1", "key": "GDP growth", "valueText": "1.0% (2025)"},
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "GDP growth was 1.0% in 2025.",
                "sentences": [
                    {"id": "left-s-1-1", "text": "GDP growth was 1.0% in 2025."},
                ],
            }
        ],
    }

    class DuplicateTextLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [
                {
                    "key": "GDP growth",
                    "valueText": "1.0% (2025)",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                    "confidence": 0.9,
                }
            ]

    pool = build_attribute_pool(article, "left", DuplicateTextLLM())

    assert len(pool) == 1
    assert pool[0]["sourceIds"] == ["left-info-1"]
    assert pool[0]["relatedSourceIds"] == ["left-s-1-1"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd server && python3 -m pytest tests/test_attribute_pool.py::test_build_attribute_pool_merges_duplicate_text_evidence_into_infobox -q
```

Expected: FAIL because duplicate text attributes are appended instead of merged.

- [ ] **Step 3: Implement deduplication in `attribute_pool.py`**

Add helpers:

```python
def _merge_or_append_text_attribute(pool, attribute):
    duplicate = _find_duplicate_attribute(pool, attribute)
    if duplicate is None:
        pool.append(attribute)
        return
    related = list(duplicate.get("relatedSourceIds") or [])
    for source_id in attribute.get("sourceIds") or []:
        if source_id not in related and source_id not in duplicate.get("sourceIds", []):
            related.append(source_id)
    if related:
        duplicate["relatedSourceIds"] = related


def _find_duplicate_attribute(pool, attribute):
    key = _normalized_key(attribute.get("key"))
    value = _normalized_value(attribute.get("valueText"))
    for existing in pool:
        if _normalized_key(existing.get("key")) != key:
            continue
        if _normalized_value(existing.get("valueText")) == value:
            return existing
    return None


def _normalized_key(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _normalized_value(value):
    return re.sub(r"[^a-z0-9.%$€£¥₩]+", " ", str(value or "").lower()).strip()
```

Replace:

```python
pool.append(attribute)
```

inside the text attribute loop with:

```python
_merge_or_append_text_attribute(pool, attribute)
```

- [ ] **Step 4: Strengthen LLM prompt**

In `server/services/llm_client.py`, update the user prompt to include:

```text
Return attributes from body text even when no matching infobox row exists.
Do not return an attribute that only restates a nearby infobox value unless the sentence is useful supporting evidence.
If a sentence supports an infobox-like fact, return the same key and valueText so the backend can merge it as related evidence.
For multi-value sentences, include structuredValues with label, value, and kind.
```

- [ ] **Step 5: Write pipeline row test for related source IDs**

Append to `server/tests/test_pipeline.py`:

```python
def test_normalize_attribute_pair_preserves_related_source_ids():
    row = normalize_attribute_pair(
        {
            "id": "left-a",
            "key": "GDP growth",
            "valueText": "1.0% (2025)",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
            "relatedSourceIds": ["left-s-1-1"],
        },
        {
            "id": "right-a",
            "key": "GDP growth",
            "valueText": "0.7% (2025)",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
            "relatedSourceIds": ["right-s-1-1"],
        },
        "GDP growth",
    )

    assert row["leftRelatedSourceIds"] == ["left-s-1-1"]
    assert row["rightRelatedSourceIds"] == ["right-s-1-1"]
```

- [ ] **Step 6: Run test to verify failure**

Run:

```bash
cd server && python3 -m pytest tests/test_pipeline.py::test_normalize_attribute_pair_preserves_related_source_ids -q
```

Expected: FAIL because row does not expose related source IDs.

- [ ] **Step 7: Add related IDs to `normalize_attribute_pair()`**

In `server/services/pipeline.py`, add to row:

```python
"leftRelatedSourceIds": list(left_attr.get("relatedSourceIds") or []),
"rightRelatedSourceIds": list(right_attr.get("relatedSourceIds") or []),
```

- [ ] **Step 8: Improve server alignment**

In `server/server.py`, replace `_align_exact_lowercase_keys()` internals with staged matching:

```python
def _align_exact_lowercase_keys(left_pool, right_pool):
    right_by_key = {}
    for attribute in right_pool:
        right_by_key.setdefault(_alignment_key(attribute.get("key")), []).append(attribute)

    used_right_ids = set()
    alignments = []
    for left_attribute in left_pool:
        key = _alignment_key(left_attribute.get("key"))
        candidates = [item for item in right_by_key.get(key, []) if item.get("id") not in used_right_ids]
        if not candidates:
            candidates = _label_overlap_candidates(left_attribute, right_pool, used_right_ids)
        if not candidates:
            continue
        right_attribute = candidates[0]
        used_right_ids.add(right_attribute.get("id"))
        alignments.append({
            "left": left_attribute,
            "right": right_attribute,
            "label": left_attribute.get("key") or right_attribute.get("key") or key,
        })
    return alignments
```

Add `_label_overlap_candidates()`:

```python
def _label_overlap_candidates(left_attribute, right_pool, used_right_ids):
    left_labels = _structured_or_numeric_labels(left_attribute)
    if not left_labels:
        return []
    candidates = []
    for right_attribute in right_pool:
        if right_attribute.get("id") in used_right_ids:
            continue
        right_labels = _structured_or_numeric_labels(right_attribute)
        overlap = left_labels & right_labels
        if overlap:
            candidates.append((len(overlap), right_attribute))
    return [item for _, item in sorted(candidates, key=lambda pair: -pair[0])]
```

Keep this conservative; do not add LLM alignment in this task unless an existing configured client path already exists.

- [ ] **Step 9: Run backend tests**

Run:

```bash
cd server && python3 -m pytest -q
```

Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add server/services/attribute_pool.py server/services/llm_client.py server/server.py server/services/pipeline.py server/tests/test_attribute_pool.py server/tests/test_compare_api.py server/tests/test_pipeline.py
git commit -m "feat: merge text evidence into comparison rows"
```

---

## Task 7: Hover Highlights Include Related Body Text

**Files:**
- Modify: `client/src/js/sessionStore.js`
- Modify: `client/src/components/compoents_base/CompareTable.vue`
- Modify: `client/src/components/compoents_base/ParentComponent.vue`

- [ ] **Step 1: Update highlight data model**

In `client/src/js/sessionStore.js`, add:

```js
relatedHighlightedSourceIds: [],
```

Update `clearInteractionState()`:

```js
this.relatedHighlightedSourceIds = [];
```

Add:

```js
highlightWithRelated(primaryIds, relatedIds = []) {
	this.highlightedSourceIds = primaryIds || [];
	this.relatedHighlightedSourceIds = relatedIds || [];
}
```

Update `clearHighlight()`:

```js
this.highlightedSourceIds = [];
this.relatedHighlightedSourceIds = [];
```

- [ ] **Step 2: Use related IDs from table hover**

In `CompareTable.vue`, replace side hover calls:

```vue
@mouseover="highlightSide(row, 'left')"
```

Add helper:

```js
const highlightSide = (row, side) => {
	const primary = side === "left" ? row.leftSourceIds : row.rightSourceIds;
	const related = side === "left" ? row.leftRelatedSourceIds : row.rightRelatedSourceIds;
	store.highlightWithRelated(primary || [], related || []);
};
```

Update `highlightBoth(row)`:

```js
const highlightBoth = row => {
	store.highlightWithRelated(
		[...(row.leftSourceIds || []), ...(row.rightSourceIds || [])],
		[...(row.leftRelatedSourceIds || []), ...(row.rightRelatedSourceIds || [])]
	);
	store.revealSourceIds = [...(row.leftSourceIds || []), ...(row.rightSourceIds || [])];
	store.revealRequestId += 1;
};
```

- [ ] **Step 3: Render related highlight style**

In `ParentComponent.vue`, clear and apply `.source-related-highlight`:

```js
root.querySelectorAll(".source-highlight, .source-related-highlight, .source-pinned").forEach(node => {
	node.classList.remove("source-highlight", "source-related-highlight", "source-pinned");
});

store.relatedHighlightedSourceIds.forEach(id => {
	root.querySelectorAll(`[data-source-id="${cssEscape(id)}"]`).forEach(node => {
		node.classList.add("source-related-highlight");
	});
});
```

Update watch dependencies:

```js
() => [store.highlightedSourceIds, store.relatedHighlightedSourceIds, store.pinnedSourceIds, article.value?.html]
```

Add CSS:

```css
:deep([data-source-id].source-related-highlight) {
	background: rgba(255, 242, 184, 0.48);
	outline: 1px solid rgba(217, 144, 47, 0.28);
	border-radius: 2px;
}
```

- [ ] **Step 4: Browser verify hover**

Use a row with both infobox and related text source IDs. Hover:

- left value cell
- right value cell
- middle attribute cell

Expected:

- primary source receives stronger `.source-highlight`
- related sentence receives softer `.source-related-highlight`
- side hover does not scroll the other article
- middle hover reveals primary source

- [ ] **Step 5: Commit**

```bash
git add client/src/js/sessionStore.js client/src/components/compoents_base/CompareTable.vue client/src/components/compoents_base/ParentComponent.vue
git commit -m "feat: highlight related text evidence from table rows"
```

---

## Task 8: Full Verification and Iteration

**Files:**
- No new files required.
- Verify all touched files.

- [ ] **Step 1: Run all frontend utility tests**

Run:

```bash
node client/tests/comparisonDisplayPlan.test.cjs
node client/tests/structuredValueDisplay.test.cjs
node client/tests/compareTableStructuredValues.test.cjs
node client/tests/creditRatingDisplay.test.cjs
node client/tests/textComparisonDisplay.test.cjs
node client/tests/chartValueDisplay.test.cjs
node client/tests/mergedComparisonData.test.cjs
node client/tests/sessionHistory.test.cjs
node client/tests/proportionalPreview.test.cjs
```

Expected: all pass.

- [ ] **Step 2: Run backend tests**

Run:

```bash
cd server && python3 -m pytest -q
```

Expected: all pass.

- [ ] **Step 3: Build frontend**

Run:

```bash
cd client && npm run build
```

Expected: build succeeds. Existing asset-size warnings are acceptable.

- [ ] **Step 4: Restart backend if needed**

Run:

```bash
lsof -nP -iTCP:8888 -sTCP:LISTEN
```

If no process is listening, run:

```bash
cd server && python3 server.py
```

Keep the process running for browser verification.

- [ ] **Step 5: Browser verify table**

At `http://127.0.0.1:8080/`, load Korea vs Japan and verify:

- `GDP`: `nominal: ...`, `PPP: ...` on both sides, same order and colors.
- `FDI stock`: shared `Inward` same color, unmatched `Abroad`/`Outward` muted.
- `GDP growth`: left shows year labels; right single value stays simple.
- `Fiscal year`: no fake label and no `1:`.
- rows top-align and no longer look vertically scattered.

- [ ] **Step 6: Browser verify URL controls**

Capture screenshots:

- collapsed state
- expanded state

Expected:

- collapsed state reads as compact session strip.
- expanded state is quiet and does not dominate viewport.

- [ ] **Step 7: Browser verify chart modals**

Open:

- FDI merged chart
- GDP merged chart
- GDP growth merged chart
- FDI enlarged chart

Expected:

- merged chart type follows source chart semantics.
- line source remains line.
- modal has no large summary/raw cards.
- x-axis labels use value labels such as `Inward`, `Abroad`, `nominal`, or `PPP` whenever row values contain labels; year appears in tooltip or subtitle instead of replacing the dimension label.
- legend and axes remain visible.

- [ ] **Step 8: Browser verify hover evidence**

Hover a table row with related text IDs.

Expected:

- infobox source and body sentence/paragraph both highlight.
- primary and related highlight styles are distinguishable.

- [ ] **Step 9: Fix visual regressions if any**

If browser screenshots still show inconsistent table styles, identify the specific row and add a targeted unit test before changing code.

- [ ] **Step 10: Final commit**

If Task 8 required fixes:

```bash
git add <changed-files>
git commit -m "fix: polish comparison verification issues"
```

If no fixes were needed, do not create an empty commit.
