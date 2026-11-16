# Étudiant 4 · Données (Cosmos DB + Blob Storage)

Modèle de données : [`contracts/cosmos-model.md`](../../contracts/cosmos-model.md).

| Ressource | Choix | Pourquoi |
|---|---|---|
| Cosmos DB for NoSQL | **free tier** (1000 RU/s + 25 Go) en dev | 0 DH ; un seul compte free tier par abonnement |
| Conteneur `stock` | partition `/partnerId` | un partenaire ne lit que **sa** partition (isolation + coût) |
| Conteneur `nonces` | TTL activé | les nonces s'effacent seuls après 10 min |
| Blob `raw` | copies brutes immuables | piste d'audit |
| Blob `exports` | exports d'impact | rapports donateurs / conseil |

## En local

Le service `data-init` de `local/docker-compose.yml` exécute `init_local.py` au démarrage.

- Explorateur Cosmos (émulateur) : http://localhost:1234
- Blob (Azurite) : utiliser **Azure Storage Explorer** → « Local storage emulator »

## À faire

- [ ] module Terraform `infra/azure/modules/data/` (compléter : politique d'immuabilité sur `raw`, cycle de vie Cool/Archive)
- [ ] index Cosmos (exclure les champs non filtrés pour réduire les RU)
- [ ] recherche vectorielle (champ `embedding`) si le temps le permet
