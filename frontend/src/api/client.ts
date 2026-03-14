import axios from "axios";

const API_BASE = "/api";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

export const dashboardApi = {
  getStats: () => api.get("/dashboard/stats"),
  getCharts: () => api.get("/dashboard/charts"),
};

export const factorsApi = {
  list: (params?: { active_only?: boolean; sort_by?: string; limit?: number }) =>
    api.get("/factors", { params }),
  getDetail: (id: string) => api.get(`/factors/${id}`),
  deactivate: (id: string) => api.post(`/factors/${id}/deactivate`),
};

export const agentApi = {
  run: (data: { research_goal?: string; tickers?: string[]; start_date?: string; end_date?: string }) =>
    api.post("/agent/run", data),
  getStatus: () => api.get("/agent/status"),
  wsUrl: () => {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    return `${proto}//${host}/api/agent/ws`;
  },
};

export const dataApi = {
  getStatus: () => api.get("/data/status"),
  update: (data: { tickers_to_add?: string[]; start_date?: string; end_date?: string; re_evaluate?: boolean }) =>
    api.post("/data/update", data),
};

export const backtestApi = {
  run: (data: { factor_expression: string; top_pct?: number; bottom_pct?: number; transaction_cost?: number }) =>
    api.post("/backtest/run", data),
};

export const reportsApi = {
  list: () => api.get("/reports"),
  getContent: (filename: string) => api.get(`/reports/${filename}`),
  downloadUrl: (filename: string) => `${API_BASE}/reports/${filename}/download`,
};

export const logsApi = {
  getLogs: (limit?: number) => api.get("/logs", { params: { limit } }),
};
