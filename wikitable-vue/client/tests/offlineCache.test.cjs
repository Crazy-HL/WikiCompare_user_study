const assert = require("assert");
const fs = require("fs");
const path = require("path");

const clientRoot = path.join(__dirname, "..");
const mainSource = fs.readFileSync(path.join(clientRoot, "src", "main.js"), "utf8");
const div2Source = fs.readFileSync(path.join(clientRoot, "src", "components", "Div2.vue"), "utf8");
const urlCompareSource = fs.readFileSync(path.join(clientRoot, "src", "components", "UrlCompareForm.vue"), "utf8");
const sessionStoreSource = fs.readFileSync(path.join(clientRoot, "src", "js", "sessionStore.js"), "utf8");
const offlineSupportPath = path.join(clientRoot, "src", "js", "offlineSupport.js");
const serviceWorkerPath = path.join(clientRoot, "public", "offline-sw.js");

assert(fs.existsSync(offlineSupportPath), "offlineSupport.js should define offline helpers");
assert(fs.existsSync(serviceWorkerPath), "public/offline-sw.js should provide the app-shell service worker");

const offlineSupportSource = fs.readFileSync(offlineSupportPath, "utf8");
const serviceWorkerSource = fs.readFileSync(serviceWorkerPath, "utf8");

assert(
	mainSource.includes("registerOfflineCache") &&
		mainSource.includes("registerOfflineCache();"),
	"main.js should register the offline app-shell cache"
);

assert(
	offlineSupportSource.includes("WIKICOMPARE_OFFLINE_MESSAGE") &&
		offlineSupportSource.includes("navigator.onLine === false") &&
		offlineSupportSource.includes("serviceWorker.register") &&
		offlineSupportSource.includes("offline-sw.js"),
	"offlineSupport should expose offline status/message helpers and register the service worker"
);

assert(
	serviceWorkerSource.includes("wikicompare-app-shell") &&
		serviceWorkerSource.includes("self.addEventListener(\"install\"") &&
		serviceWorkerSource.includes("self.addEventListener(\"fetch\"") &&
		serviceWorkerSource.includes("request.mode === \"navigate\"") &&
		serviceWorkerSource.includes("cache.put(request, response.clone())"),
	"offline service worker should precache the app shell and dynamically cache same-origin assets"
);

assert(
	sessionStoreSource.includes("isOfflineNow") &&
		sessionStoreSource.includes("WIKICOMPARE_OFFLINE_MESSAGE") &&
		sessionStoreSource.includes("this.error = WIKICOMPARE_OFFLINE_MESSAGE"),
	"sessionStore should block Compare/Regenerate backend calls while offline but keep cached sessions visible"
);

assert(
	div2Source.includes("isOfflineNow") &&
		div2Source.includes("WIKICOMPARE_OFFLINE_MESSAGE") &&
		div2Source.includes("当前离线") &&
		div2Source.indexOf("if (isOfflineNow())") < div2Source.indexOf("postJson(\"api/ask\"") &&
		div2Source.indexOf("if (isOfflineNow())") < div2Source.indexOf("postJson(\"api/analyze-attribute\""),
	"question answering and attribute analysis should show a clear offline message instead of calling backend/LLM"
);

assert(
	urlCompareSource.includes("offlineStatusText") &&
		urlCompareSource.includes("window.addEventListener(\"offline\"") &&
		urlCompareSource.includes("store.error") &&
		urlCompareSource.includes("当前离线"),
	"URL compare controls should surface offline state to users"
);

console.log("offlineCache tests passed");
