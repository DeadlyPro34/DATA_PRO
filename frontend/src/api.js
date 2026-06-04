import axios from "axios";

// Use relative URL so Vite's proxy forwards to Django (no CORS issues!)
const BASE_URL = import.meta.env.VITE_API_URL || "/api";
const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      try {
        const refresh = localStorage.getItem("refresh_token");
        if (refresh) {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh });
          localStorage.setItem("access_token", data.access);
          err.config.headers.Authorization = `Bearer ${data.access}`;
          return api(err.config);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  register: (data) => api.post("/auth/register/", data),
  login:    (data) => api.post("/auth/login/", data),
  refresh:  (data) => api.post("/auth/refresh/", data),
  me:       ()     => api.get("/auth/me/"),
};

export const datasetAPI = {
  list:   ()    => api.get("/datasets/"),
  detail: (id)  => api.get(`/datasets/${id}/`),
  delete: (id)  => api.delete(`/datasets/${id}/delete/`),

  rows: (id, page=1, size=200) =>
    api.get(`/datasets/${id}/rows/?page=${page}&size=${size}`),

  upload: (file, name, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    if (name) form.append("name", name);
    return api.post("/datasets/upload/", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
  },

  // NEW: Save cell edit to PostgreSQL
  updateCell: (id, rowIndex, column, value) =>
    api.patch(`/datasets/${id}/update_cell/`, { row_index: rowIndex, column, value }),

  // NEW: Add empty row
  addRow: (id, data = {}) =>
    api.post(`/datasets/${id}/add_row/`, { data }),

  // NEW: Delete row
  deleteRow: (id, rowIndex) =>
    api.delete(`/datasets/${id}/delete_row/${rowIndex}/`),

  // NEW: Add column
  addColumn: (id, columnName, defaultValue = "") =>
    api.post(`/datasets/${id}/add_column/`, { column_name: columnName, default_value: defaultValue }),

  // NEW: Excel functions
  applyFunction: (id, fn, column, resultColumn = null) =>
    api.post(`/datasets/${id}/function/`, { function: fn, column, result_column: resultColumn }),

  // NEW: AI Pandas (Groq-generated code runs on backend)
  aiPandas: (id, code) =>
    api.post(`/datasets/${id}/ai_pandas/`, { code }),

  // NEW: Auto Dashboard — pure Pandas analysis, no AI API needed
  autoDashboard: (id) =>
    api.get(`/datasets/${id}/auto_dashboard/`),
};

export default api;
