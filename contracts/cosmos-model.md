# Modèle de données

## Cosmos DB for NoSQL — base `foodaid`

| Conteneur | Clé de partition | Contenu | Écrit par |
|---|---|---|---|
| `stock` | `/partnerId` | un document par mouvement de denrée (IN / OUT) | workers |
| `alerts` | `/partnerId` | alertes de péremption | workers |
| `nonces` | `/id` | nonces déjà vus (TTL 600 s) | API |

Document `stock` :

```json
{
  "id": "DON-0001:FARINE-25KG",
  "donationId": "DON-0001",
  "partnerId": "P2",
  "sku": "FARINE-25KG",
  "label": "Farine 25 kg",
  "quantity": 40,
  "unit": "unite",
  "movement": "IN",
  "expiryDate": "2027-03-01",
  "receivedAt": "2026-11-16T10:00:00Z"
}
```

L'`id` est déterministe (`donationId:sku`) : rejouer un lot réécrit le même document au lieu d'en créer un nouveau (**idempotence**).

## Blob Storage

| Conteneur | Contenu | Accès |
|---|---|---|
| `raw` | copie brute de chaque lot reçu : `raw/AAAA-MM-JJ/<donationId>.json` | API (écriture), Auditor (lecture) |
| `exports` | exports d'impact (CSV) pour donateurs et conseil | workers (écriture) |
