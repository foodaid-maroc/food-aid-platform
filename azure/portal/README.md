# Étudiant 5 · Accès (Static Web Apps + Entra ID)

Portail React (Vite) avec connexion **MSAL** et 4 rôles. Le RBAC est appliqué **côté API** ; le portail ne fait qu'afficher.

## Lancer en local (sans Entra ID)

```bash
docker compose -f local/docker-compose.yml up -d --build   # l'API locale doit tourner
cd azure/portal
cp .env.example .env          # VITE_AUTH_MODE=mock
npm install
npm run dev                   # http://localhost:5173
```

En mode **mock**, un sélecteur de rôle remplace la connexion : on peut développer toutes les pages sans compte Azure.

## Passer à Entra ID

1. Portail Azure → **Microsoft Entra ID** → **App registrations** → `foodaid-portal` (SPA, redirect URI `http://localhost:5173` + URL du site).
2. **App roles** : `Staff`, `Partner`, `Donor`, `Auditor` (valeurs exactes de `contracts/jwt-claims.md`).
3. **Expose an API** : scope `access_as_user` → `VITE_API_SCOPE`.
4. **Enterprise applications** → `foodaid-portal` → **Users and groups** : un compte de test par rôle.
5. `.env` : `VITE_AUTH_MODE=entra` + tenant ID + client ID.

Si le tenant ESI bloque la création d'App registrations : utiliser la gestion des rôles intégrée de Static Web Apps (invitations) et le mode `x-ms-client-principal` déjà géré par l'API.

## Déploiement

- **Plan Free** en dev : `VITE_API_BASE=https://<app-api>.azurecontainerapps.io` + CORS côté API.
- **Plan Standard** (semaine de la démo) : *linked backend* → `/api` est relayé vers Container Apps.

## À faire

- [ ] vraies pages par rôle (graphiques, filtres)
- [ ] claim `partnerId` (voir `contracts/jwt-claims.md`)
- [ ] module Terraform `infra/azure/modules/access/`
