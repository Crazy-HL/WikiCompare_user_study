import { postJson } from "@/api";
import axios from "axios";

const API_ROOT = "http://localhost:8888/";

export const getExperimentConfig = () => axios.get(`${API_ROOT}api/experiment/config`).then(response => response.data);
export const startExperiment = participantCode => postJson("api/experiment/start", { participantCode });
export const getQuestions = materialId => axios.get(`${API_ROOT}api/experiment/questions`, { params: { materialId } }).then(response => response.data);
export const completeExperiment = payload => postJson("api/experiment/complete", payload);
export const adminLogin = password => postJson("api/admin/login", { password });
