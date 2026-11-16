# Étudiant 3 · Calcul (Container Apps : api + workers, Service Bus)

| App | Rôle | Échelle |
|---|---|---|
| `azure/api` | `POST /ingest` (AWS, HMAC) et `GET /query` (portail, JWT + rôle) | 1–3 réplicas (HTTP) |
| `azure/workers` | consomme la file Service Bus `batches`, écrit le stock et les alertes dans Cosmos DB | 0–5 réplicas (règle KEDA sur la file) |

## Lancer les tests

```bash
cd azure/api
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## En local

`docker compose -f local/docker-compose.yml up -d --build` lance `api` (port 8080) et `workers` avec les émulateurs.

```bash
curl http://localhost:8080/health
curl -H "X-Dev-Role: Staff" http://localhost:8080/query
curl -H "X-Dev-Role: Partner" -H "X-Dev-Partner: P2" http://localhost:8080/query
```

## Variables d'environnement (Azure)

| Variable | Valeur |
|---|---|
| `AUTH_MODE` | `entra` |
| `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE` | fournis par l'Étudiant 5 |
| `HMAC_SECRET` | référence Key Vault `hmac-ingest-key` (Étudiant 6) |
| `BLOB_ACCOUNT_URL`, `COSMOS_ENDPOINT`, `SERVICEBUS_NAMESPACE` | sorties Terraform ; accès par **identité managée** |

## À faire

- [ ] prévisions de la demande + exports d'impact dans Blob `exports`
- [ ] module Terraform `infra/azure/modules/compute/` (vérifier la règle KEDA)
- [ ] impact par donateur (`donor_impact`)
