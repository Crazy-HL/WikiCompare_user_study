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
		height: 100vh;
		width: 100%;
		overflow: hidden;
		background-color: #f9f9f9;
	}

	#root {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		height: calc(100vh - 50px);
		width: 100%;
		padding: 5px;
		background-color: #f9f9f9;
		overflow: hidden;
	}

	.div {
		flex: 1;
		margin: 0 1px;
		padding: 0px;
		background-color: #ffffff;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
		overflow-y: auto;
		max-height: calc(100vh - 60px);
		transition: box-shadow 0.3s ease, transform 0.3s ease;
	}

	.div:hover {
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15); /* 悬停时阴影加深 */
		transform: translateY(-6px); /* 悬停时轻微上移 */
	}

	/* 自定义滚动条样式 */
	.div::-webkit-scrollbar {
		width: 8px; /* 滚动条宽度 */
	}

	.div::-webkit-scrollbar-track {
		background-color: #f1f1f1; /* 滚动条轨道颜色 */
		border-radius: 4px; /* 轨道圆角 */
	}

	.div::-webkit-scrollbar-thumb {
		background-color: #c1c1c1; /* 滚动条滑块颜色 */
		border-radius: 4px; /* 滑块圆角 */
	}

	.div::-webkit-scrollbar-thumb:hover {
		background-color: #a8a8a8; /* 悬停时滑块颜色 */
	}
</style>
