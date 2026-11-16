import { useEffect, useState } from "react";
import { fetchQuery } from "../api";

const TITLES = {
  Staff: "Stock et livraisons — tous les partenaires",
  Partner: "Mes livraisons",
  Donor: "Impact de mes dons",
  Auditor: "Historique complet (lecture seule)",
};

/** Une seule vue ; ce qui s'affiche dépend des données renvoyées par l'API (RBAC côté serveur). */
export default function RoleView({ roles, auth }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const role = roles[0];

  useEffect(() => {
    setError(null);
    fetchQuery(auth).then(setData).catch((e) => setError(e.message));
  }, [auth.token, auth.mockRole, auth.mockPartner]);

  if (!role) return <p>Aucun rôle attribué : contactez l'administrateur.</p>;
  if (error) return <p style={{ color: "crimson" }}>Erreur API : {error}</p>;
  if (!data) return <p>Chargement…</p>;

  const cols = data.items.length ? Object.keys(data.items[0]) : [];
  return (
    <section>
      <h2>{TITLES[role] ?? role}</h2>
      <p>{data.items.length} ligne(s)</p>
      <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {data.items.map((it, i) => (
            <tr key={i}>{cols.map((c) => <td key={c}>{String(it[c] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
