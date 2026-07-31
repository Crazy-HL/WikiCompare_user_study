const WIKICOMPARE_OFFLINE_MESSAGE =
	"当前离线：已缓存的文章和图表仍可查看，需要后端或大模型的功能暂不可用。";

const isOfflineNow = () =>
	typeof navigator !== "undefined" && navigator.onLine === false;

const registerOfflineCache = () => {
	if (
		typeof window === "undefined" ||
		!("serviceWorker" in navigator)
	) {
		return;
	}

	window.addEventListener("load", () => {
		navigator.serviceWorker.register("/offline-sw.js").catch(error => {
			console.warn("WikiCompare offline cache registration failed", error);
		});
	});
};

module.exports = {
	isOfflineNow,
	registerOfflineCache,
	WIKICOMPARE_OFFLINE_MESSAGE,
};
