<template>
	<section class="admin-login-card">
		<h1>研究管理后台</h1>
		<p>请输入研究人员管理密码。</p>
		<form @submit.prevent="submitLogin">
			<label for="admin-password">管理密码</label>
			<input
				id="admin-password"
				v-model="password"
				type="password"
				autocomplete="current-password"
				placeholder="Password"
				:disabled="loading" />
			<p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
			<button type="submit" :disabled="loading || !password.trim()">
				{{ loading ? "正在登录..." : "登录" }}
			</button>
		</form>
	</section>
</template>

<script setup>
	import { ref } from "vue";
	import { adminLogin } from "@/experiment/experimentApi";

	const emit = defineEmits(["authenticated"]);

	const password = ref("");
	const loading = ref(false);
	const errorMessage = ref("");

	const submitLogin = async () => {
		if (!password.value.trim()) return;
		loading.value = true;
		errorMessage.value = "";
		try {
			const response = await adminLogin(password.value);
			const token = response?.token;
			if (!token) throw new Error("登录响应缺少管理令牌。");
			emit("authenticated", token);
		} catch (error) {
			errorMessage.value = error.response?.data?.error || error.message || "登录失败，请检查密码。";
		} finally {
			password.value = "";
			loading.value = false;
		}
	};
</script>

<style scoped>
	.admin-login-card {
		width: min(460px, 100%);
		border: 1px solid #dbe4ee;
		border-radius: 20px;
		padding: 32px;
		background: #ffffff;
		box-shadow: 0 18px 50px rgba(15, 23, 42, 0.1);
		box-sizing: border-box;
	}

	h1 {
		margin: 0 0 10px;
		font-size: 28px;
		color: #172033;
	}

	p {
		margin: 0 0 24px;
		color: #64748b;
	}

	form {
		display: grid;
		gap: 12px;
	}

	label {
		font-weight: 800;
		color: #334155;
	}

	input {
		border: 1px solid #cbd5e1;
		border-radius: 12px;
		padding: 12px 14px;
		font-size: 16px;
		outline: none;
	}

	input:focus {
		border-color: #2563eb;
		box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
	}

	button {
		border: 0;
		border-radius: 12px;
		padding: 12px 16px;
		background: #2563eb;
		color: #ffffff;
		font-size: 16px;
		font-weight: 900;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.55;
	}

	.error-message {
		margin: 0;
		border: 1px solid #fecaca;
		border-radius: 10px;
		padding: 10px 12px;
		background: #fff7f7;
		color: #991b1b;
	}
</style>
