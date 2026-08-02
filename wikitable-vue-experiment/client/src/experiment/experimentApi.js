import { postJson } from "@/api";
import axios from "axios";

const API_ROOT = "http://localhost:8888/";

export const getExperimentConfig = () => axios.get(`${API_ROOT}api/experiment/config`).then(response => response.data);
export const startExperiment = participantCode => postJson("api/experiment/start", { participantCode });
export const getQuestions = materialId => axios.get(`${API_ROOT}api/experiment/questions`, { params: { materialId } }).then(response => response.data);
export const completeExperiment = payload => postJson("api/experiment/complete", payload);
export const adminLogin = password => postJson("api/admin/login", { password });

export const adminHeaders = token => ({ headers: { "X-Admin-Token": token } });
export const adminQuestions = (token, materialId) => axios.get(`${API_ROOT}api/admin/questions`, { ...adminHeaders(token), params: { materialId } }).then(response => response.data);
export const adminSubmissions = token => axios.get(`${API_ROOT}api/admin/submissions`, adminHeaders(token)).then(response => response.data);
export const adminFreezeQuestions = (token, materialId) => axios.post(`${API_ROOT}api/admin/questions/freeze`, { materialId }, adminHeaders(token)).then(response => response.data);
export const adminUnfreezeQuestions = (token, materialId) => axios.post(`${API_ROOT}api/admin/questions/unfreeze`, { materialId }, adminHeaders(token)).then(response => response.data);
export const adminGenerateQuestions = (token, materialId, rawQuestions) => axios.post(`${API_ROOT}api/admin/questions/generate`, { materialId, rawQuestions }, adminHeaders(token)).then(response => response.data);
export const adminDownloadExport = (token, exportPath) => axios.get(`${API_ROOT}${exportPath}`, { ...adminHeaders(token), responseType: "blob" }).then(response => response.data);
