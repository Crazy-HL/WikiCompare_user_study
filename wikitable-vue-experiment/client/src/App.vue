<script>
	import general from "./components/general.vue";
	export default {
		name: "App",
		components: {
			general
		},
		mounted() {
			this.getData();
		},
		methods: {
			getData() {
				let self = this;
				// api.get("data", { papername: "rmap1" }, data => {
				// 	Data = data;
				// 	store.state.loaddata = Math.random();
				// });
				// api.get("", {}, data => {
				// 	console.log("@@@", data);
				// });
			}
		}
	};
</script>

<template>
	<general></general>
</template>

<style scoped></style>
