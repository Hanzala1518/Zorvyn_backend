import axios from "axios";

// In production on Vercel, NEXT_PUBLIC_API_URL is left empty ("") so that all
// /api/* requests go through Next.js rewrites (next.config.ts) to the Render
// backend — meaning they're same-origin and CORS never fires.
// Locally, set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local.
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "",
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("finance_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("finance_token");
      localStorage.removeItem("finance_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const loginUser = (email: string, password: string) =>
  api.post("/api/auth/login", new URLSearchParams({ username: email, password }), {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

export const getMe = () => api.get("/api/auth/me");

export const changePassword = (currentPassword: string, newPassword: string) =>
  api.post("/api/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });

// Transactions
export const getTransactions = (params?: object) =>
  api.get("/api/transactions/", { params });

export const createTransaction = (data: object) =>
  api.post("/api/transactions", data);

export const updateTransaction = (id: string, data: object) =>
  api.patch(`/api/transactions/${id}`, data);

export const deleteTransaction = (id: string) =>
  api.delete(`/api/transactions/${id}`);

export const exportTransactions = (params?: object) =>
  api.get("/api/transactions/export", { params, responseType: "blob" });

// Dashboard
export const getDashboardSummary = () => api.get("/api/dashboard/summary");

export const getCategoryBreakdown = (type?: string) =>
  api.get("/api/dashboard/category-breakdown", { params: { type } });

export const getMonthlyTrends = (year?: number) =>
  api.get("/api/dashboard/monthly-trends", { params: { year } });

export const getWeeklyTrends = (weeks?: number) =>
  api.get("/api/dashboard/weekly-trends", { params: { weeks } });

export const getRecentActivity = (limit?: number) =>
  api.get("/api/dashboard/recent-activity", { params: { limit } });

export const getTopCategories = (limit?: number) =>
  api.get("/api/dashboard/top-categories", { params: { limit } });

// Users
export const getUsers = (params?: object) => api.get("/api/users/", { params });

export const createUser = (data: object) => api.post("/api/users", data);

export const updateUser = (id: string, data: object) =>
  api.patch(`/api/users/${id}`, data);

export const deleteUser = (id: string) => api.delete(`/api/users/${id}`);

// Registration
export const registerUser = (data: object) => api.post("/api/auth/register", data);

// Admin approval
export const getPendingApprovals = () => api.get("/api/admin/pending-approvals");
export const approveUser = (id: string) => api.post(`/api/admin/approve/${id}`);
export const rejectUser = (id: string, reason: string) =>
  api.post(`/api/admin/reject/${id}`, { reason });

// Budgets
export const getBudgets = () => api.get("/api/budgets");
export const setBudget = (data: object) => api.post("/api/budgets", data);
export const deleteBudget = (id: string) => api.delete(`/api/budgets/${id}`);

// Notifications
export const getNotifications = () => api.get("/api/notifications/");
export const markNotificationRead = (id: string) =>
  api.patch(`/api/notifications/${id}/read`);
export const markAllRead = () => api.patch("/api/notifications/read-all");

// Analytics
export const getHealthScore = () => api.get("/api/analytics/health-score");
export const getRecurring = () => api.get("/api/analytics/recurring");
export const getVelocity = () => api.get("/api/analytics/velocity");
