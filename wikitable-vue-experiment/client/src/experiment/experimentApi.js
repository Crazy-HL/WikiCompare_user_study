import axios from "axios";

const configuredBase = (process.env.VUE_APP_EXPERIMENT_API_BASE || "").trim();
const API_ROOT = configuredBase ? configuredBase.replace(/\/?$/, "/") : "/";
const apiUrl = path => `${API_ROOT}${path.replace(/^\/+/, "")}`;

const postJson = (path, payload, config = {}) => axios
	.post(apiUrl(path), payload, { headers: { "Content-Type": "application/json", ...(config.headers || {}) }, ...config })
	.then(response => response.data);

export const getExperimentConfig = () => axios.get(apiUrl("api/experiment/config")).then(response => response.data);
export const startExperiment = participantCode => postJson("api/experiment/start", { participantCode });
export const getQuestions = materialId => axios.get(apiUrl("api/experiment/questions"), { params: { materialId } }).then(response => response.data);
export const getStaticTable = materialId => axios.get(apiUrl("api/experiment/static-table"), { params: { materialId } }).then(response => response.data);
export const completeExperiment = payload => postJson("api/experiment/complete", payload);
export const adminLogin = password => postJson("api/admin/login", { password });

export const adminHeaders = token => ({ headers: { "X-Admin-Token": token } });
export const adminQuestions = (token, materialId) => axios.get(apiUrl("api/admin/questions"), { ...adminHeaders(token), params: { materialId } }).then(response => response.data);
export const adminSubmissions = token => axios.get(apiUrl("api/admin/submissions"), adminHeaders(token)).then(response => response.data);
export const adminFreezeQuestions = (token, materialId) => postJson("api/admin/questions/freeze", { materialId }, adminHeaders(token));
export const adminUnfreezeQuestions = (token, materialId) => postJson("api/admin/questions/unfreeze", { materialId }, adminHeaders(token));
export const adminGenerateQuestions = (token, materialId, rawQuestions) => postJson("api/admin/questions/generate", { materialId, rawQuestions }, adminHeaders(token));
export const adminStaticTable = (token, materialId) => axios.get(apiUrl("api/admin/static-table"), { ...adminHeaders(token), params: { materialId } }).then(response => response.data);
export const adminSaveStaticTable = (token, materialId, rows) => postJson("api/admin/static-table", { materialId, rows }, adminHeaders(token));
export const adminFreezeStaticTable = (token, materialId) => postJson("api/admin/static-table/freeze", { materialId }, adminHeaders(token));
export const adminUnfreezeStaticTable = (token, materialId) => postJson("api/admin/static-table/unfreeze", { materialId }, adminHeaders(token));
export const adminDownloadExport = (token, exportPath) => axios.get(apiUrl(exportPath), { ...adminHeaders(token), responseType: "blob" }).then(response => response.data);
export const experimentApiUrl = apiUrl;
