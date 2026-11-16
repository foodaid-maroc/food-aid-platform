# Contrats d'échange

Ces fichiers sont **l'accord commun de l'équipe**. Chacun code contre eux, avec des données d'exemple (`examples/`), sans attendre le code des autres.

| Fichier | Entre qui et qui | Responsables |
|---|---|---|
| [`lot.schema.json`](lot.schema.json) | Sources → API Gateway → SQS → Lambda → API Azure | Étudiants 1, 2, 3 |
| [`hmac.md`](hmac.md) | Lambda (AWS) → `POST /ingest` (Azure) | Étudiants 2, 3, 6 |
| [`servicebus-message.schema.json`](servicebus-message.schema.json) | API → Service Bus → workers | Étudiant 3 |
| [`cosmos-model.md`](cosmos-model.md) | workers / API ↔ Cosmos DB, Blob | Étudiants 3, 4 |
| [`jwt-claims.md`](jwt-claims.md) | Entra ID → portail → `GET /query` | Étudiants 3, 5 |
| [`openapi.yaml`](openapi.yaml) | Routes de l'API Azure | Étudiants 3, 5 |

Toute modification = PR `contract(...)` approuvée par les responsables listés.
