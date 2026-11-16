import { useState } from "react";
import { AUTH_MODE, ROLES } from "./authConfig";
import EntraSession from "./EntraSession";
import RoleView from "./pages/RoleView";

const styles = {
  page: { fontFamily: "system-ui, sans-serif", maxWidth: 1000, margin: "32px auto", padding: "0 16px" },
  bar: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 16 },
};

/** Mode mock : choisir un rôle pour développer sans Entra ID. */
function MockSession() {
  const [role, setRole] = useState("Staff");
  const [partner, setPartner] = useState("P2");
  return (
    <>
      <div style={styles.bar}>
        <strong>Mode local (mock)</strong> · rôle :
        {ROLES.map((r) => (
          <button key={r} onClick={() => setRole(r)} disabled={r === role}>{r}</button>
        ))}
        {role === "Partner" && (
          <label> partnerId <input value={partner} onChange={(e) => setPartner(e.target.value)} size={4} /></label>
        )}
      </div>
      <RoleView roles={[role]} auth={{ mockRole: role, mockPartner: partner }} />
    </>
  );
}

export default function App() {
  return (
    <main style={styles.page}>
      <h1>Banque Alimentaire du Maroc · Traçabilité</h1>
      {AUTH_MODE === "entra" ? <EntraSession /> : <MockSession />}
    </main>
  );
}
