<template>
	<!-- <MainComponent
		pageTitle="LeBron James"
		divId="div1"
		selectContentClass="selectContent1" /> -->
	<!-- <ParentComponent
		pageTitle="Kevin Durant"
		divId="div1"
		selectContentClass="selectContent1"
		:linkedOutline="linkedOutline" /> -->
	<ParentComponent
		pageTitle="Economy of South Korea"
		revision="1273871505"
		divId="div1"
		selectContentClass="selectContent1"
		:linkedOutline="linkedOutline" />
</template>

<script setup>
	import BaseWikipedia from "@/components/BaseWikipedia.vue";
	import ParentComponent from "@/components/compoents_base/ParentComponent.vue";
	// const linkedOutline = [
	// 	{ leftId: "heading-0-div1", rightId: "heading-0-div3" },
	// 	{ leftId: "heading-3-div1", rightId: "heading-3-div3" },
	// 	{ leftId: "heading-9-div1", rightId: "heading-12-div3" },
	// 	{ leftId: "heading-23-div1", rightId: "heading-13-div3" },
	// 	{ leftId: "heading-24-div1", rightId: "heading-14-div3" },
	// 	{ leftId: "heading-25-div1", rightId: "heading-19-div3" },
	// 	{ leftId: "heading-26-div1", rightId: "heading-15-div3" },
	// 	{ leftId: "heading-28-div1", rightId: "heading-16-div3" },
	// 	{ leftId: "heading-30-div1", rightId: "heading-17-div3" },
	// 	{ leftId: "heading-32-div1", rightId: "heading-32-div3" },
	// 	{ leftId: "heading-33-div1", rightId: "heading-33-div3" },
	// 	{ leftId: "heading-34-div1", rightId: "heading-35-div3" },
	// 	{ leftId: "heading-35-div1", rightId: "heading-37-div3" }
	// ];

	const linkedOutline = [
		{ leftId: "heading-0-div1", rightId: "heading-0-div3" },
		{ leftId: "heading-10-div1", rightId: "heading-11-div3" }
	];
</script>
