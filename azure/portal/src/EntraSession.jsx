import { useEffect, useState } from "react";
import { AuthenticatedTemplate, UnauthenticatedTemplate, useMsal } from "@azure/msal-react";
import { apiRequest } from "./authConfig";
import RoleView from "./pages/RoleView";

/** Mode entra : connexion MSAL, rôles lus dans le jeton, appels API avec Bearer. */
export default function EntraSession() {
  const { instance, accounts } = useMsal();
  const account = accounts[0];
  const [token, setToken] = useState(null);

  useEffect(() => {
    if (!account) return;
    instance
      .acquireTokenSilent({ ...apiRequest, account })
      .catch(() => instance.acquireTokenPopup({ ...apiRequest, account }))
      .then((r) => setToken(r.accessToken));
  }, [account, instance]);

  const roles = account?.idTokenClaims?.roles ?? [];

  return (
    <>
      <UnauthenticatedTemplate>
        <button onClick={() => instance.loginRedirect(apiRequest)}>Se connecter</button>
      </UnauthenticatedTemplate>
      <AuthenticatedTemplate>
        <p>
          Connecté : {account?.username} · rôles : {roles.join(", ") || "aucun"}{" "}
          <button onClick={() => instance.logoutRedirect()}>Se déconnecter</button>
        </p>
        {token && <RoleView roles={roles} auth={{ token }} />}
      </AuthenticatedTemplate>
    </>
  );
}
