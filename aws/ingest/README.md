# Étudiant 1 · Ingestion (API Gateway + SQS)

**Rôle :** seule porte d'entrée publique. Reçoit les webhooks CMI et les formulaires partenaires et les dépose dans SQS, sans code (intégration directe API Gateway → SQS).

## Ce qui est à faire

| # | Tâche | Où |
|---|---|---|
| 1 | File `foodaid-lots` + DLQ `foodaid-lots-dlq` (redrive après 3 échecs) | `infra/aws/modules/ingest/` |
| 2 | API REST `foodaid-ingest` : `POST /donations` → intégration AWS `SQS SendMessage` | `infra/aws/modules/ingest/` |
| 3 | Rôle IAM qui autorise **seulement** API Gateway à écrire dans la file | idem |
| 4 | Limitation de débit (throttling) + validation du corps (JSON Schema `contracts/lot.schema.json`) | idem |
| 5 | Alarme CloudWatch si la DLQ contient des messages | idem |

## Tester en local (ElasticMQ remplace SQS)

```bash
docker compose -f local/docker-compose.yml up -d
pip install boto3
python aws/ingest/send_test_donation.py --local                       # envoie contracts/examples/lot-formulaire.json
python aws/ingest/send_test_donation.py --local --file contracts/examples/lot-cmi.json
```

Console ElasticMQ : http://localhost:9325

## Tester sur AWS (pendant une session d'intégration)

```bash
python aws/ingest/send_test_donation.py --url https://<id>.execute-api.<region>.amazonaws.com/dev/donations
```
