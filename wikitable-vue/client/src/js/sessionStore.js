import { reactive } from "vue";
import { postJson } from "@/api";

export const sessionStore = reactive({
	session: null,
	isLoading: false,
	error: "",
	highlightedSourceIds: [],
	pinnedSourceIds: [],

	async loadSession(leftUrl, rightUrl) {
		this.isLoading = true;
		this.error = "";
		this.highlightedSourceIds = [];
		this.pinnedSourceIds = [];
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

	clearHighlight() {
		this.highlightedSourceIds = [];
	},

	pin(sourceIds) {
		this.pinnedSourceIds = sourceIds || [];
	}
});
