# Étudiant 6 · Sécurité (Key Vault + Log Analytics)

## Secrets (Key Vault `kv-foodaid-dev`)

| Secret | Utilisé par | Comment |
|---|---|---|
| `hmac-ingest-key` | app api (Azure), Lambda (copie dans SSM) | référence de secret Container Apps via identité managée |
| `cosmos-…`, `servicebus-…` | — | **inutile** : accès par identité managée + RBAC, pas de clé |

Règles :

- Key Vault en **mode RBAC** ; l'identité managée de chaque app n'a que `Key Vault Secrets User` ;
- aucun membre de l'équipe n'a besoin de lire les secrets en production ;
- rotation de `hmac-ingest-key` : nouvelle version dans Key Vault + mise à jour SSM.

## Journaux (Log Analytics `log-foodaid-dev`)

Envoyés via les *diagnostic settings* : Container Apps, Key Vault, Service Bus, Cosmos DB, Static Web Apps.
Requêtes prêtes à l'emploi : [`queries.kql`](queries.kql).

## Alertes à créer

| Alerte | Condition |
|---|---|
| Signatures refusées | plus de 10 `ingest_rejected` en 5 min |
| DLQ non vide | messages dans la DLQ Service Bus |
| Accès Key Vault refusé | `ResultSignature == "Forbidden"` |

## Coût

Log Analytics : **plafond journalier** (`daily_quota_gb`) défini dans Terraform, rétention 30 jours.

## À faire

- [ ] module Terraform `infra/azure/modules/security/` (compléter les diagnostic settings et les alertes)
- [ ] scan des secrets dans la CI (déjà branché : gitleaks)
