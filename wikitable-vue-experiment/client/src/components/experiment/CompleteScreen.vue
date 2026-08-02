<template>
	<section class="complete-screen">
		<div class="message-card">
			<h1>实验已完成，感谢参与。</h1>
			<p>请告知研究人员你已经完成全部两个阶段。</p>
		</div>
	</section>
</template>

<style scoped>
	.complete-screen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
		box-sizing: border-box;
		background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	.message-card {
		max-width: 620px;
		padding: 38px;
		border-radius: 22px;
		background: #ffffff;
		border: 1px solid #bfdbfe;
		text-align: center;
		box-shadow: 0 22px 60px rgba(37, 99, 235, 0.14);
	}

	h1 {
		margin: 0 0 12px;
		color: #1d4ed8;
		font-size: clamp(28px, 4vw, 38px);
		line-height: 1.2;
	}

	p {
		margin: 0;
		color: #475569;
		font-size: 16px;
	}
</style>
