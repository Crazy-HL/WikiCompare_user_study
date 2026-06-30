<template>
	<div id="app-shell">
		<UrlCompareForm />
		<div id="root">
			<Div1 class="div" />
			<Div2 class="div" />
			<Div3 class="div" />
		</div>
	</div>
</template>

<script setup>
	import UrlCompareForm from "./UrlCompareForm.vue";
	import Div1 from "./Div1.vue";
	import Div2 from "./Div2.vue";
	import Div3 from "./Div3.vue";
</script>

<style scoped>
	#app-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		width: 100%;
		overflow: hidden;
		background:
			linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%);
		color: #1f2937;
		font-family:
			Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
			"Segoe UI", sans-serif;
	}

	#root {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		flex: 1;
		min-height: 0;
		width: 100%;
		padding: 10px;
		box-sizing: border-box;
		background: transparent;
		overflow: hidden;
		gap: 10px;
	}

	.div {
		flex: 1;
		min-width: 0;
		margin: 0;
		padding: 0;
		background-color: #ffffff;
		border: 1px solid rgba(190, 201, 216, 0.82);
		border-radius: 8px;
		overflow-y: auto;
		max-height: 100%;
		box-shadow:
			0 1px 2px rgba(15, 23, 42, 0.04),
			0 10px 24px rgba(15, 23, 42, 0.06);
	}

	.div::-webkit-scrollbar {
		width: 8px;
	}

	.div::-webkit-scrollbar-track {
		background-color: #f3f6fa;
		border-radius: 999px;
	}

	.div::-webkit-scrollbar-thumb {
		background-color: #b9c4d1;
		border: 2px solid #f3f6fa;
		border-radius: 999px;
	}

	.div::-webkit-scrollbar-thumb:hover {
		background-color: #94a3b8;
	}
</style>
