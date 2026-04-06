export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "analyst" | "viewer";
  status: string;
}

export const getToken = () =>
  typeof window !== "undefined" ? localStorage.getItem("finance_token") : null;

export const setToken = (t: string) => localStorage.setItem("finance_token", t);

export const getUser = (): AuthUser | null => {
  if (typeof window === "undefined") return null;
  const u = localStorage.getItem("finance_user");
  return u ? JSON.parse(u) : null;
};

export const setUser = (u: AuthUser) =>
  localStorage.setItem("finance_user", JSON.stringify(u));

export const logout = () => {
  localStorage.removeItem("finance_token");
  localStorage.removeItem("finance_user");
  window.location.href = "/login";
};

export const isAuthenticated = () => !!getToken();

export const formatINR = (amount: number): string =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

export const hasRole = (user: AuthUser | null, ...roles: AuthUser["role"][]): boolean =>
  !!user && roles.includes(user.role);

export const isAdmin = (user: AuthUser | null) => hasRole(user, "admin");
export const isAnalystOrAbove = (user: AuthUser | null) => hasRole(user, "admin", "analyst");

