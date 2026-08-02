<template>
	<section class="admin-panel">
		<header class="panel-header">
			<div>
				<h2>提交记录</h2>
				<p>查看参与者提交、阶段顺序、Q1-Q6 答案、证据与计时明细。</p>
			</div>
			<button type="button" :disabled="loading" @click="loadSubmissions">刷新</button>
		</header>

		<div v-if="message" class="notice success">{{ message }}</div>
		<div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>

		<section class="export-card">
			<h3>导出链接</h3>
			<div class="export-row">
				<code>/api/admin/export/submissions.csv</code>
				<button type="button" :disabled="downloading" @click="downloadExport('api/admin/export/submissions.csv', 'submissions.csv')">
					下载 submissions.csv
				</button>
			</div>
			<div class="export-row">
				<code>/api/admin/export/answers.csv</code>
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
						<th>details</th>
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
						<td>
							<details>
								<summary>查看答案与计时</summary>
								<div class="submission-detail">
									<p><strong>startedAt:</strong> {{ submission.startedAt || "—" }}</p>
									<p><strong>startedAtMs/completedAtMs:</strong> {{ submission.startedAtMs ?? "—" }} / {{ submission.completedAtMs ?? "—" }}</p>
									<section v-for="stage in submission.stages || []" :key="`${submission.experimentId}-${stage.stageIndex}`" class="stage-detail">
										<h4>Stage {{ stage.stageIndex }} · {{ stage.condition }} · {{ stage.materialId }}</h4>
										<p><strong>stageDurationMs:</strong> {{ stage.stageDurationMs ?? "—" }} · <strong>stageStartedAtMs:</strong> {{ stage.stageStartedAtMs ?? "—" }} · <strong>stageSubmittedAtMs:</strong> {{ stage.stageSubmittedAtMs ?? "—" }}</p>
										<table class="answers-table">
											<thead>
												<tr>
													<th>questionId</th>
													<th>answer</th>
													<th>primarySource</th>
													<th>evidence</th>
													<th>durationMs</th>
												</tr>
											</thead>
											<tbody>
												<tr v-for="answer in stage.answers || []" :key="`${stage.stageIndex}-${answer.questionId}`">
													<td><strong>{{ answer.questionId }}</strong><br><small>{{ answer.questionText }}</small></td>
													<td>{{ answer.answer || "—" }}</td>
													<td>{{ answer.primarySource || "—" }}</td>
													<td>leftEvidence: {{ answer.leftEvidence || "—" }}<br>rightEvidence: {{ answer.rightEvidence || "—" }}</td>
													<td>{{ answer.durationMs ?? "—" }}<br><small>{{ answer.answerStartedAtMs ?? "—" }} → {{ answer.submittedAtMs ?? "—" }}</small></td>
												</tr>
											</tbody>
										</table>
									</section>
								</div>
							</details>
						</td>
					</tr>
					<tr v-if="!loading && !submissions.length">
						<td colspan="7" class="empty-state">暂无提交记录。</td>
					</tr>
					<tr v-if="loading">
						<td colspan="7" class="empty-state">正在加载提交记录...</td>
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
	.admin-panel { display: grid; gap: 20px; }
	.panel-header { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; }
	h2 { margin: 0 0 8px; font-size: 28px; color: #172033; }
	p { margin: 0; color: #64748b; }
	.export-card, .table-card, .notice { border: 1px solid #dbe4ee; border-radius: 16px; padding: 16px; background: #ffffff; }
	h3 { margin: 0 0 12px; font-size: 18px; color: #172033; }
	.export-card { display: grid; gap: 12px; }
	.export-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; border-radius: 12px; padding: 12px; background: #f8fafc; }
	code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; font-size: 13px; color: #334155; word-break: break-all; }
	.table-card { overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; min-width: 980px; }
	th, td { border-bottom: 1px solid #e2e8f0; padding: 12px 10px; text-align: left; vertical-align: top; font-size: 14px; }
	th { background: #f8fafc; color: #334155; font-weight: 900; position: sticky; top: 0; }
	td { color: #172033; }
	button { border: 1px solid #cbd5e1; border-radius: 12px; padding: 10px 14px; background: #ffffff; color: #172033; font-weight: 900; white-space: nowrap; cursor: pointer; }
	button:disabled { cursor: not-allowed; opacity: 0.55; }
	.notice.success { border-color: #bbf7d0; background: #f0fdf4; color: #166534; }
	.notice.error { border-color: #fecaca; background: #fff7f7; color: #991b1b; }
	.empty-state { padding: 22px; color: #64748b; text-align: center; }
	summary { cursor: pointer; font-weight: 900; color: #1d4ed8; }
	.submission-detail { display: grid; gap: 12px; min-width: 760px; }
	.stage-detail { border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; background: #f8fafc; }
	h4 { margin: 0 0 8px; color: #172033; }
	.answers-table { min-width: 720px; background: #ffffff; }
	small { color: #64748b; }
	@media (max-width: 760px) { .panel-header, .export-row { display: grid; } }
</style>
