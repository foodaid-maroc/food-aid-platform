import { API_BASE } from "./authConfig";

/** Appelle GET /query. En mode mock : en-têtes X-Dev-*. En mode entra : jeton Bearer. */
export async function fetchQuery({ token, mockRole, mockPartner }) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (mockRole) {
    headers["X-Dev-Role"] = mockRole;
    if (mockPartner) headers["X-Dev-Partner"] = mockPartner;
  }
  const res = await fetch(`${API_BASE}/query`, { headers });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}
