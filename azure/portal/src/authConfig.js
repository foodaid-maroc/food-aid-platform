export const AUTH_MODE = import.meta.env.VITE_AUTH_MODE || "mock";
export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID}`,
    redirectUri: window.location.origin,
  },
  cache: { cacheLocation: "sessionStorage" },
};

export const apiRequest = { scopes: [import.meta.env.VITE_API_SCOPE].filter(Boolean) };

export const ROLES = ["Staff", "Partner", "Donor", "Auditor"];
