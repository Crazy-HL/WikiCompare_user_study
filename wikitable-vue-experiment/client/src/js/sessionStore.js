import { reactive } from "vue";
import { postJson } from "@/api";
const {
	isOfflineNow,
	WIKICOMPARE_OFFLINE_MESSAGE,
} = require("@/js/offlineSupport");

const {
	addSessionToHistory,
	findHistoryByKey,
	findHistoryByUrls,
	loadHistory,
	removeHistoryByKey,
	saveHistory,
	sessionPairKey,
} = require("@/js/sessionHistory");

export const isInfoboxSourceId = sourceId => /-info-\d+$/.test(String(sourceId || ""));

export const pinnedRevealSourceIds = (sourceIds = [], relatedSourceIds = []) => {
	const primary = sourceIds || [];
	const related = relatedSourceIds || [];
	const primaryInfobox = primary.filter(isInfoboxSourceId);
	const otherPrimary = primary.filter(sourceId => !isInfoboxSourceId(sourceId));
	return primaryInfobox.length
		? [...primaryInfobox, ...related, ...otherPrimary]
		: [...related, ...otherPrimary];
};

export const applySessionTitles = (session, options = {}) => {
	if (!session || (!options.leftTitle && !options.rightTitle)) return session;
	return {
		...session,
		articles: {
			...(session.articles || {}),
			left: {
				...(session.articles?.left || {}),
				title: options.leftTitle || session.articles?.left?.title
			},
			right: {
				...(session.articles?.right || {}),
				title: options.rightTitle || session.articles?.right?.title
			}
		}
	};
};

export const isHttpUrl = value => {
	try {
		const parsed = new URL(String(value || "").trim());
		return parsed.protocol === "http:" || parsed.protocol === "https:";
	} catch (_error) {
		return false;
	}
};

export const buildSessionPayload = (leftInput, rightInput, options = {}) => {
	const payload = { forceRefresh: options.forceRefresh === true };
	const left = String(leftInput || "").trim();
	const right = String(rightInput || "").trim();
	if (isHttpUrl(left)) {
		payload.leftUrl = left;
	} else {
		payload.leftContent = left;
	}
	if (isHttpUrl(right)) {
		payload.rightUrl = right;
	} else {
		payload.rightContent = right;
	}
	if (options.leftTitle) payload.leftTitle = options.leftTitle;
	if (options.rightTitle) payload.rightTitle = options.rightTitle;
	return payload;
};

const initialHistory = loadHistory();
if (initialHistory[0]?.session) {
	saveHistory(undefined, initialHistory);
}

export const sessionStore = reactive({
	session: initialHistory[0]?.session || null,
	history: initialHistory,
	activeHistoryKey: initialHistory[0]?.key || "",
	isLoading: false,
	error: "",
	highlightedSourceIds: [],
	relatedHighlightedSourceIds: [],
	pinnedSourceIds: [],
	pinnedRelatedSourceIds: [],
	pinnedHighlightKey: "",
	revealSourceIds: [],
	revealBehavior: "auto",
	revealRequestId: 0,

	async loadSession(leftUrl, rightUrl, options = {}) {
		const forceRefresh = options.forceRefresh === true;
		const ensureBackendSession = options.ensureBackendSession === true;
		const canUseUrlHistory = isHttpUrl(leftUrl) && isHttpUrl(rightUrl);
		if (!forceRefresh && canUseUrlHistory) {
			const cachedRecord = findHistoryByUrls(this.history, leftUrl, rightUrl);
			if (cachedRecord?.session) {
				const cachedSession = applySessionTitles(cachedRecord.session, options);
				this.applySession(cachedSession);
				if (!ensureBackendSession) {
					return;
				}
				if (isOfflineNow()) {
					this.error = WIKICOMPARE_OFFLINE_MESSAGE;
					return;
				}
				this.isLoading = true;
				try {
					await this.restoreSessionToBackend(cachedSession);
					this.error = "";
					return;
				} catch (_restoreError) {
					// A stale or malformed browser cache should not block the participant;
					// regenerate only when the lightweight backend restoration fails.
				} finally {
					this.isLoading = false;
				}
			}
		}
		await this.loadFreshSession(leftUrl, rightUrl, { ...options, forceRefresh });
	},

	async loadFreshSession(leftUrl, rightUrl, options = {}) {
		if (isOfflineNow()) {
			this.error = WIKICOMPARE_OFFLINE_MESSAGE;
			return;
		}

		this.isLoading = true;
		this.error = "";
		this.clearInteractionState();
		try {
			const payload = buildSessionPayload(leftUrl, rightUrl, options);
			const session = await postJson("api/compare-session", payload);
			this.applySession(applySessionTitles(session, options));
		} catch (error) {
			this.error =
				error.response?.data?.error ||
				error.message ||
				"Failed to load comparison session";
		} finally {
			this.isLoading = false;
		}
	},

	async restoreSessionToBackend(session) {
		return postJson("api/compare-session/restore", { session });
	},

	async selectHistory(key) {
		const record = findHistoryByKey(this.history, key);
		if (!record) return;
		if (record.session) {
			this.applySession(record.session);
			return;
		}
		await this.loadSession(record.leftUrl, record.rightUrl);
	},

	removeHistory(key) {
		this.history = removeHistoryByKey(this.history, key);
		if (this.activeHistoryKey === key) {
			this.activeHistoryKey = "";
		}
		saveHistory(undefined, this.history);
	},

	async regenerateCurrent() {
		const leftUrl = this.session?.articles?.left?.url;
		const rightUrl = this.session?.articles?.right?.url;
		if (!leftUrl || !rightUrl) return;
		await this.loadSession(leftUrl, rightUrl, { forceRefresh: true });
	},

	applySession(session) {
		this.error = "";
		this.session = session;
		this.activeHistoryKey = sessionPairKey(session);
		this.history = addSessionToHistory(this.history, session);
		saveHistory(undefined, this.history);
		this.clearInteractionState();
	},

	clearInteractionState() {
		this.highlightedSourceIds = [];
		this.relatedHighlightedSourceIds = [];
		this.pinnedSourceIds = [];
		this.pinnedRelatedSourceIds = [];
		this.pinnedHighlightKey = "";
		this.revealSourceIds = [];
		this.revealBehavior = "auto";
		this.revealRequestId = 0;
	},

	highlight(sourceIds, relatedSourceIds = []) {
		this.highlightedSourceIds = sourceIds || [];
		this.relatedHighlightedSourceIds = relatedSourceIds || [];
	},

	highlightAndReveal(sourceIds, relatedSourceIds = [], options = {}) {
		this.highlight(sourceIds, relatedSourceIds);
		this.revealSourceIds = sourceIds || [];
		this.revealBehavior = options.behavior || "smooth";
		this.revealRequestId += 1;
	},

	clearHighlight() {
		this.highlightedSourceIds = [];
		this.relatedHighlightedSourceIds = [];
	},

	pin(sourceIds, relatedSourceIds = [], key = "") {
		this.pinnedSourceIds = sourceIds || [];
		this.pinnedRelatedSourceIds = relatedSourceIds || [];
		this.pinnedHighlightKey = key || "";
	},

	clearPinnedHighlight() {
		this.pinnedSourceIds = [];
		this.pinnedRelatedSourceIds = [];
		this.pinnedHighlightKey = "";
	},

	togglePinnedHighlight(key, sourceIds, relatedSourceIds = []) {
		if (this.pinnedHighlightKey === key) {
			this.clearPinnedHighlight();
			return false;
		}
		this.pin(sourceIds, relatedSourceIds, key);
		this.revealSourceIds = pinnedRevealSourceIds(sourceIds, relatedSourceIds);
		this.revealBehavior = "auto";
		this.revealRequestId += 1;
		return true;
	}
});
