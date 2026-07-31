<template>
	<div :class="contentClasses" v-html="content" @mouseup="onMouseUp"></div>
</template>

<script setup>
	import { computed } from "vue";

	const props = defineProps({
		content: {
			type: String,
			required: true
		},
		sourceKind: {
			type: String,
			default: "wikipedia"
		}
	});

	const emit = defineEmits(["select"]);

	const isOpenFactBookContent = computed(() =>
		props.sourceKind === "web" &&
		/(openfactbook\.org|group\/field|Flag of |Map of )/i.test(props.content)
	);

	const contentClasses = computed(() => [
		"wikipedia-content",
		props.sourceKind === "web" ? "source-web" : "source-wikipedia",
		isOpenFactBookContent.value ? "openfactbook-profile openfactbook-metric-grid openfactbook-field-card" : ""
	]);

	const onMouseUp = () => {
		const selection = window.getSelection();
		if (!selection.rangeCount) return;

		const range = selection.getRangeAt(0);
		const selectedHtml = range.cloneContents();

		// 创建临时容器
		const tempDiv = document.createElement("div");
		tempDiv.appendChild(selectedHtml);

		// 判断选中的内容是否包含表格
		const table = tempDiv.querySelector("table");
		if (table) {
			table.classList.add("custom-table");
			emit("select", tempDiv.innerHTML);
		} else {
			const text = selection.toString().trim();
			if (text) {
				emit("select", text);
			}
		}
	};
</script>

<style scoped>
	.wikipedia-content {
		width: 100%;
		box-sizing: border-box;
		padding: 8px 16px 30px;
		color: #243447;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
		font-size: 13px;
		line-height: 1.62;
		overflow-wrap: anywhere;
	}

	.wikipedia-content.source-web {
		padding: 8px 18px 34px;
		color: #263647;
		font-size: 12.8px;
		line-height: 1.62;
	}

	.wikipedia-content.source-web.openfactbook-profile {
		padding: 12px 18px 34px;
		background:
			linear-gradient(135deg, rgba(255, 248, 237, 0.92) 0%, rgba(239, 248, 251, 0.92) 52%, rgba(252, 246, 255, 0.92) 100%);
		color: #243447;
	}

	.wikipedia-content :deep(h1),
	.wikipedia-content :deep(h2),
	.wikipedia-content :deep(h3),
	.wikipedia-content :deep(h4) {
		clear: none;
		margin: 19px 0 8px;
		color: #172033;
		line-height: 1.25;
		letter-spacing: 0;
	}

	.wikipedia-content :deep(h1) {
		font-size: 22px;
	}

	.wikipedia-content :deep(h2) {
		padding-bottom: 5px;
		border-bottom: 1px solid #d6e0ea;
		font-size: 18px;
	}

	.wikipedia-content :deep(h3) {
		font-size: 15px;
	}

	.wikipedia-content :deep(p) {
		margin: 8px 0 9px;
	}

	.wikipedia-content.source-web :deep(p) {
		margin: 8px 0 10px;
		max-width: 72ch;
	}

	.wikipedia-content :deep(a) {
		color: #3867a8;
		text-decoration: none;
	}

	.wikipedia-content :deep(a:hover) {
		text-decoration: underline;
	}

	.wikipedia-content :deep(table) {
		display: block;
		max-width: 100%;
		margin: 10px 0;
		overflow-x: auto;
		border-collapse: collapse;
		font-size: 12px;
		background: #ffffff;
		border: 1px solid #d7dee8;
		border-radius: 6px;
	}

	.wikipedia-content.source-web :deep(table) {
		width: auto;
		max-width: 100%;
		margin: 12px 0;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
	}

	.wikipedia-content :deep(th),
	.wikipedia-content :deep(td) {
		padding: 5px 7px;
		border: 1px solid #dbe3ee;
		vertical-align: top;
	}

	.wikipedia-content :deep(th) {
		background: #f4f7fb;
		color: #1f2937;
		font-weight: 600;
	}

	.wikipedia-content :deep(.infobox),
	.wikipedia-content :deep(.sidebar),
	.wikipedia-content :deep(.toccolours) {
		float: right;
		display: table;
		width: min(230px, 46%);
		margin: 0 0 10px 13px;
		overflow: visible;
		font-size: 10.5px;
		line-height: 1.3;
		border: 1px solid #cfd8e5;
		border-radius: 6px;
		border-collapse: collapse;
		background: #fbfdff;
		box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
	}

	.wikipedia-content :deep(.infobox th),
	.wikipedia-content :deep(.infobox td),
	.wikipedia-content :deep(.sidebar th),
	.wikipedia-content :deep(.sidebar td),
	.wikipedia-content :deep(.toccolours th),
	.wikipedia-content :deep(.toccolours td) {
		padding: 3px 5px;
	}

	.wikipedia-content :deep(img) {
		max-width: 100%;
		height: auto;
		border-radius: 4px;
	}

	.wikipedia-content.source-web :deep(img),
	.wikipedia-content.source-web :deep(video),
	.wikipedia-content.source-web :deep(iframe) {
		display: block;
		max-width: 100%;
		height: auto;
		margin: 8px 0;
		border-radius: 6px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(img[alt^="Flag of"]) {
		width: min(176px, 62%);
		max-height: 138px;
		object-fit: cover;
		margin: 8px 0 18px;
		border: 1px solid rgba(51, 65, 85, 0.24);
		border-radius: 10px;
		box-shadow:
			0 12px 24px rgba(15, 23, 42, 0.12),
			0 2px 5px rgba(15, 23, 42, 0.08);
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(img[alt^="Map of"]) {
		width: 100%;
		max-height: 180px;
		object-fit: contain;
		margin: 10px 0 14px;
		padding: 8px;
		border: 1px solid rgba(203, 213, 225, 0.82);
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.78);
	}

	.wikipedia-content.source-web :deep(svg) {
		display: inline-block;
		width: 1em;
		height: 1em;
		max-width: 18px;
		max-height: 18px;
		vertical-align: -0.15em;
	}

	.wikipedia-content :deep(.navbox),
	.wikipedia-content :deep(.metadata),
	.wikipedia-content :deep(.reflist),
	.wikipedia-content :deep(.references),
	.wikipedia-content :deep(.hatnote),
	.wikipedia-content :deep(.ambox),
	.wikipedia-content :deep(.toc),
	.wikipedia-content :deep(.mw-editsection) {
		display: none !important;
	}

	.wikipedia-content.source-web :deep(nav),
	.wikipedia-content.source-web :deep(header),
	.wikipedia-content.source-web :deep(footer),
	.wikipedia-content.source-web :deep(form),
	.wikipedia-content.source-web :deep(button),
	.wikipedia-content.source-web :deep([role="navigation"]),
	.wikipedia-content.source-web :deep([role="button"]),
	.wikipedia-content.source-web :deep([class*="fixed" i]),
	.wikipedia-content.source-web :deep([class*="sticky" i]),
	.wikipedia-content.source-web :deep([class*="breadcrumb" i]),
	.wikipedia-content.source-web :deep([class*="cookie" i]),
	.wikipedia-content.source-web :deep([class*="social" i]),
	.wikipedia-content.source-web :deep([class*="share" i]) {
		display: none !important;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(h1) {
		margin: 10px 0 5px;
		color: #172033;
		font-family: Georgia, "Times New Roman", serif;
		font-size: 28px;
		font-weight: 760;
		line-height: 1.05;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(h2) {
		margin-top: 18px;
		padding-bottom: 6px;
		border-bottom: 1px solid rgba(148, 163, 184, 0.32);
		font-size: 17px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(h3),
	.wikipedia-content.source-web.openfactbook-profile :deep(h4) {
		margin: 7px 0 5px;
		font-size: 13px;
		font-weight: 780;
		line-height: 1.24;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.glass-card) {
		margin: 10px 0;
		padding: 12px;
		border: 1px solid rgba(203, 213, 225, 0.8);
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.82);
		box-shadow:
			0 1px 2px rgba(15, 23, 42, 0.05),
			0 8px 18px rgba(15, 23, 42, 0.05);
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="group/field"]) {
		margin: 8px 0;
		padding: 11px 12px;
		border-left: 3px solid rgba(56, 103, 168, 0.44);
		background: rgba(255, 255, 255, 0.9);
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="group/field"] p) {
		margin: 4px 0 0;
		max-width: none;
		color: #334155;
		line-height: 1.5;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.flex) {
		display: flex;
		gap: 8px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.grid) {
		display: grid;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.items-start) {
		align-items: flex-start;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.items-center) {
		align-items: center;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.items-end) {
		align-items: flex-end;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.justify-between) {
		justify-content: space-between;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.flex-1) {
		flex: 1 1 0;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.relative) {
		position: relative;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.absolute) {
		position: absolute;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.overflow-hidden) {
		overflow: hidden;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="lg:grid-cols-5"]) {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 8px;
		margin: 14px 0 18px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="stat-card"]) {
		min-height: 90px;
		padding: 10px;
		border: 1px solid rgba(203, 213, 225, 0.82);
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.86);
		box-shadow:
			0 1px 2px rgba(15, 23, 42, 0.05),
			0 7px 16px rgba(15, 23, 42, 0.05);
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="stat-card"] p) {
		margin: 0;
		max-width: none;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="stat-card"] p:first-child) {
		color: #64748b;
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.03em;
		text-transform: uppercase;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="stat-card"] p:last-child) {
		margin-top: 7px;
		color: #172033;
		font-family: Georgia, "Times New Roman", serif;
		font-size: 18px;
		font-weight: 720;
		line-height: 1.18;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="stat-card"] svg) {
		width: 18px;
		height: 18px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.mb-12) {
		margin: 18px 0 22px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="md:grid-cols-2"]) {
		display: grid;
		grid-template-columns: 1fr;
		gap: 10px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.mt-6) {
		margin-top: 10px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.mt-8) {
		margin-top: 18px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep(.mt-4) {
		margin-top: 10px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="h-40"]) {
		height: 132px;
		overflow: visible !important;
		margin-bottom: 18px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="h-20"]) {
		height: 84px;
		overflow: visible !important;
		margin-bottom: 12px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="chart-bar"]) {
		position: relative;
		display: flex !important;
		flex: 1 1 0;
		height: 100%;
		min-width: 4px;
		flex-direction: column;
		justify-content: flex-end;
		cursor: pointer;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="chart-bar"] > div) {
		width: 100%;
		min-height: 2px;
		border-radius: 3px 3px 0 0;
		transition: filter 0.16s ease;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class~="chart-bar"]:hover > div) {
		filter: brightness(1.08);
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="bg-accent-500"]) {
		background: linear-gradient(180deg, rgba(180, 91, 71, 0.92), rgba(180, 91, 71, 0.34));
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="bg-purple-500"]) {
		background: linear-gradient(180deg, rgba(168, 85, 247, 0.92), rgba(168, 85, 247, 0.36));
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="bg-emerald-500"]) {
		background: linear-gradient(180deg, rgba(52, 199, 142, 0.7), rgba(52, 199, 142, 0.28));
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="-bottom-5"]) {
		bottom: -18px;
		width: max-content;
		white-space: nowrap;
		line-height: 1;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="left-1/2"]) {
		left: 50%;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="-translate-x-1/2"]) {
		transform: translateX(-50%);
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="text-[10px]"]) {
		font-size: 10px;
	}

	.wikipedia-content.source-web.openfactbook-profile :deep([class*="rounded-full"]) {
		display: inline-flex;
		align-items: center;
		width: fit-content;
		max-width: 100%;
		flex-shrink: 0;
		margin: 3px 4px 3px 0;
		padding: 4px 8px;
		border: 1px solid rgba(203, 213, 225, 0.75);
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.7);
		color: #475569;
		font-size: 11px;
		line-height: 1.2;
		white-space: nowrap;
	}

	@media (max-width: 900px) {
		.wikipedia-content :deep(.infobox),
		.wikipedia-content :deep(.sidebar),
		.wikipedia-content :deep(.toccolours) {
			float: none;
			width: 100%;
			margin-left: 0;
		}
	}

	@media (max-width: 1180px) {
		.wikipedia-content {
			padding: 7px 12px 26px;
			font-size: 12.5px;
			line-height: 1.56;
		}

		.wikipedia-content.source-web {
			padding: 8px 12px 28px;
		}

		.wikipedia-content :deep(h1) {
			font-size: 19px;
		}

		.wikipedia-content :deep(h2) {
			font-size: 16px;
		}
	}

	@media (max-width: 760px) {
		.wikipedia-content,
		.wikipedia-content.source-web {
			padding: 6px 9px 24px;
			font-size: 12px;
			line-height: 1.5;
		}

		.wikipedia-content :deep(table) {
			font-size: 11px;
		}
	}
</style>
