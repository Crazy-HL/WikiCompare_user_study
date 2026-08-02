const durationMs = (startedAtMs, endedAtMs) => Math.max(0, Number(endedAtMs || 0) - Number(startedAtMs || 0));

const createTimingMark = (now = () => Date.now()) => {
	const startedAtMs = now();
	return {
		startedAtMs,
		submit() {
			const submittedAtMs = now();
			return {
				startedAtMs,
				submittedAtMs,
				durationMs: durationMs(startedAtMs, submittedAtMs),
			};
		},
	};
};

module.exports = {
	createTimingMark,
	durationMs,
};
