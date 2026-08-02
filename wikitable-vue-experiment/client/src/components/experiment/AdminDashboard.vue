<template>
	<section class="admin-app" :class="{ 'login-layout': !token }">
		<AdminLogin v-if="!token" @authenticated="setToken" />
		<div v-else class="dashboard-shell">
			<header class="dashboard-header">
				<div>
					<p class="eyebrow">WikiCompare Experiment</p>
					<h1>研究管理后台</h1>
				</div>
				<button type="button" @click="logout">退出登录</button>
			</header>

			<nav class="tab-nav" aria-label="管理后台标签页">
				<button
					type="button"
					:class="{ active: activeTab === 'questions' }"
					@click="activeTab = 'questions'">
					题目管理
				</button>
				<button
					type="button"
					:class="{ active: activeTab === 'submissions' }"
					@click="activeTab = 'submissions'">
					答题数据
				</button>
			</nav>

			<main class="dashboard-content">
				<AdminQuestions v-if="activeTab === 'questions'" :token="token" />
				<AdminSubmissions v-else :token="token" />
			</main>
		</div>
	</section>
</template>

<script setup>
	import { ref } from "vue";
	import AdminLogin from "./AdminLogin.vue";
	import AdminQuestions from "./AdminQuestions.vue";
	import AdminSubmissions from "./AdminSubmissions.vue";

	const token = ref("");
	const activeTab = ref("questions");

	const setToken = nextToken => {
		token.value = nextToken;
	};

	const logout = () => {
		token.value = "";
		activeTab.value = "questions";
	};
</script>

<style scoped>
	.admin-app {
		min-height: 100vh;
		box-sizing: border-box;
		padding: 28px;
		background: #eef4fb;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
		color: #172033;
	}

	.admin-app.login-layout {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.dashboard-shell {
		max-width: 1180px;
		margin: 0 auto;
		display: grid;
		gap: 20px;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		gap: 20px;
		align-items: center;
		border: 1px solid #dbe4ee;
		border-radius: 20px;
		padding: 22px;
		background: #ffffff;
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
	}

	.eyebrow {
		margin: 0 0 6px;
		font-size: 12px;
		font-weight: 900;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #2563eb;
	}

	h1 {
		margin: 0;
		font-size: 32px;
	}

	.tab-nav {
		display: flex;
		gap: 10px;
		border: 1px solid #dbe4ee;
		border-radius: 18px;
		padding: 10px;
		background: #ffffff;
	}

	button {
		border: 1px solid #cbd5e1;
		border-radius: 12px;
		padding: 10px 14px;
		background: #ffffff;
		color: #172033;
		font-weight: 900;
		cursor: pointer;
	}

	.tab-nav button.active {
		border-color: #2563eb;
		background: #2563eb;
		color: #ffffff;
	}

	.dashboard-content {
		border: 1px solid #dbe4ee;
		border-radius: 20px;
		padding: 22px;
		background: #ffffff;
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
	}

	@media (max-width: 760px) {
		.admin-app {
			padding: 14px;
		}

		.dashboard-header {
			display: grid;
		}

		.tab-nav {
			display: grid;
		}
	}
</style>
