# Étudiant 2 · Validation des lots (Lambda + DynamoDB)

**Rôle :** pour chaque message SQS, la Lambda **valide** et **normalise** le don, vérifie dans DynamoDB qu'il n'est **pas déjà traité** (idempotence), le **signe** (HMAC, voir `contracts/hmac.md`) et l'envoie à `POST /ingest` sur Azure.

## Fichiers

| Fichier | Rôle |
|---|---|
| `handler.py` | code de la Lambda (`handler(event, context)`) |
| `local_runner.py` | en local : lit ElasticMQ en boucle et appelle `handler` (remplace le déclencheur SQS) |
| `events/sqs-event.json` | événement SQS d'exemple |
| `tests/` | tests unitaires (`pytest`) |

## Lancer les tests

```bash
cd aws/logic
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## En local

Le service `lambda-runner` de `local/docker-compose.yml` exécute déjà ce code contre ElasticMQ + DynamoDB Local + l'API locale.

## Variables d'environnement

| Variable | Local | AWS |
|---|---|---|
| `IDEMPOTENCY_TABLE` | `foodaid-idempotency` | idem (Terraform) |
| `DYNAMODB_ENDPOINT` | `http://dynamodb:8000` | _(vide)_ |
| `AZURE_INGEST_URL` | `http://api:8080/ingest` | URL de l'app api (Terraform) |
| `HMAC_SECRET` | `dev-secret-change-me` | _(vide : lu depuis SSM)_ |
| `HMAC_SSM_PARAM` | _(vide)_ | `/foodaid/hmac-ingest-key` |

## À faire

- [ ] compléter `validate()` avec toutes les règles de `contracts/lot.schema.json`
- [ ] module Terraform `infra/aws/modules/logic/` (table, fonction, event source mapping avec `ReportBatchItemFailures`)
- [ ] logs structurés (JSON) pour CloudWatch
