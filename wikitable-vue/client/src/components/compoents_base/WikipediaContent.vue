<template>
	<div class="wikipedia-content" v-html="content" @mouseup="onMouseUp"></div>
</template>

<script setup>
	const props = defineProps({
		content: {
			type: String,
			required: true
		}
	});

	const emit = defineEmits(["select"]);

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

	@media (max-width: 900px) {
		.wikipedia-content :deep(.infobox),
		.wikipedia-content :deep(.sidebar),
		.wikipedia-content :deep(.toccolours) {
			float: none;
			width: 100%;
			margin-left: 0;
		}
	}
</style>
