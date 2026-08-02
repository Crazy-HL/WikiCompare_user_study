<template>
	<section class="admin-panel">
		<header class="panel-header">
			<div>
				<h2>答题数据</h2>
				<p>查看参与者提交记录，并通过带管理令牌的下载按钮导出 CSV。</p>
			</div>
			<button type="button" :disabled="loading" @click="loadSubmissions">
				{{ loading ? "正在刷新..." : "刷新" }}
			</button>
		</header>

		<div v-if="message" class="notice success">{{ message }}</div>
		<div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>

		<section class="export-card">
			<h3>导出链接</h3>
			<div class="export-row">
				<code>http://localhost:8888/api/admin/export/submissions.csv</code>
				<button type="button" :disabled="downloading" @click="downloadExport('api/admin/export/submissions.csv', 'submissions.csv')">
					下载 submissions.csv
				</button>
			</div>
			<div class="export-row">
				<code>http://localhost:8888/api/admin/export/answers.csv</code>
				<button type="button" :disabled="downloading" @click="downloadExport('api/admin/export/answers.csv', 'answers.csv')">
					下载 answers.csv
				</button>
			</div>
		</section>

		<div class="table-card">
			<table>
				<thead>
					<tr>
						<th>participantCode</th>
						<th>experimentId</th>
						<th>assignmentGroup</th>
						<th>stage count</th>
						<th>totalDurationMs</th>
						<th>completedAt</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="submission in submissions" :key="submission.experimentId || submission.participantCode">
						<td>{{ submission.participantCode || "—" }}</td>
						<td>{{ submission.experimentId || "—" }}</td>
						<td>{{ submission.assignmentGroup || "—" }}</td>
						<td>{{ stageCount(submission) }}</td>
						<td>{{ submission.totalDurationMs ?? "—" }}</td>
						<td>{{ submission.completedAt || "—" }}</td>
					</tr>
					<tr v-if="!loading && !submissions.length">
						<td colspan="6" class="empty-state">暂无提交记录。</td>
					</tr>
					<tr v-if="loading">
						<td colspan="6" class="empty-state">正在加载提交记录...</td>
					</tr>
				</tbody>
			</table>
		</div>
	</section>
</template>

<script setup>
	import { onMounted, ref } from "vue";
	import { adminDownloadExport, adminSubmissions } from "@/experiment/experimentApi";

	const props = defineProps({
		token: {
			type: String,
			required: true
		}
	});

	const submissions = ref([]);
	const loading = ref(false);
	const downloading = ref(false);
	const message = ref("");
	const errorMessage = ref("");

	const showError = error => {
		errorMessage.value = error.response?.data?.error || error.message || "操作失败，请稍后重试。";
	};

	const loadSubmissions = async () => {
		loading.value = true;
		message.value = "";
		errorMessage.value = "";
		try {
			const response = await adminSubmissions(props.token);
			submissions.value = response.submissions || [];
		} catch (error) {
			showError(error);
		} finally {
			loading.value = false;
		}
	};

	const stageCount = submission => (submission.stages || []).length;

	const downloadExport = async (path, filename) => {
		downloading.value = true;
		message.value = "";
		errorMessage.value = "";
		try {
			const blob = await adminDownloadExport(props.token, path);
			const objectUrl = window.URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = objectUrl;
			link.download = filename;
			document.body.appendChild(link);
			link.click();
			link.remove();
			window.URL.revokeObjectURL(objectUrl);
			message.value = `已开始下载 ${filename}。`;
		} catch (error) {
			showError(error);
		} finally {
			downloading.value = false;
		}
	};

	onMounted(loadSubmissions);
</script>

<style scoped>
	.admin-panel {
		display: grid;
		gap: 20px;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		gap: 20px;
		align-items: flex-start;
	}

	h2 {
		margin: 0 0 8px;
		font-size: 28px;
		color: #172033;
	}

	p {
		margin: 0;
		color: #64748b;
	}

	.export-card,
	.table-card,
	.notice {
		border: 1px solid #dbe4ee;
		border-radius: 16px;
		padding: 16px;
		background: #ffffff;
	}

	h3 {
		margin: 0 0 12px;
		font-size: 18px;
		color: #172033;
	}

	.export-card {
		display: grid;
		gap: 12px;
	}

	.export-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		border-radius: 12px;
		padding: 12px;
		background: #f8fafc;
	}

	code {
		font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
		font-size: 13px;
		color: #334155;
		word-break: break-all;
	}

	.table-card {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		min-width: 900px;
	}

	th,
	td {
		border-bottom: 1px solid #e2e8f0;
		padding: 12px 10px;
		text-align: left;
		vertical-align: top;
		font-size: 14px;
	}

	th {
		background: #f8fafc;
		color: #334155;
		font-weight: 900;
		position: sticky;
		top: 0;
	}

	td {
		color: #172033;
	}

	button {
		border: 1px solid #cbd5e1;
		border-radius: 12px;
		padding: 10px 14px;
		background: #ffffff;
		color: #172033;
		font-weight: 900;
		white-space: nowrap;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.55;
	}

	.notice.success {
		border-color: #bbf7d0;
		background: #f0fdf4;
		color: #166534;
	}

	.notice.error {
		border-color: #fecaca;
		background: #fff7f7;
		color: #991b1b;
	}

	.empty-state {
		padding: 22px;
		color: #64748b;
		text-align: center;
	}

	@media (max-width: 760px) {
		.panel-header,
		.export-row {
			display: grid;
		}
	}
</style>
