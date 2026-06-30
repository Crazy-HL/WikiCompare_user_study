import { reactive } from "vue";
import { postJson } from "@/api";

export const sessionStore = reactive({
	session: null,
	isLoading: false,
	error: "",
	highlightedSourceIds: [],
	pinnedSourceIds: [],
	revealSourceIds: [],
	revealRequestId: 0,

	async loadSession(leftUrl, rightUrl) {
		this.isLoading = true;
		this.error = "";
		this.highlightedSourceIds = [];
		this.pinnedSourceIds = [];
		this.revealSourceIds = [];
		this.revealRequestId = 0;
		try {
			this.session = await postJson("api/compare-session", { leftUrl, rightUrl });
		} catch (error) {
			this.error =
				error.response?.data?.error ||
				error.message ||
				"Failed to load comparison session";
		} finally {
			this.isLoading = false;
		}
	},

	highlight(sourceIds) {
		this.highlightedSourceIds = sourceIds || [];
	},

	highlightAndReveal(sourceIds) {
		this.highlight(sourceIds);
		this.revealSourceIds = sourceIds || [];
		this.revealRequestId += 1;
	},

	clearHighlight() {
		this.highlightedSourceIds = [];
	},

	pin(sourceIds) {
		this.pinnedSourceIds = sourceIds || [];
	}
});
