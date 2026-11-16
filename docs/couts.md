# Coûts : règles de l'équipe

> Le cloud se paie **à l'heure où les ressources existent**, pas à l'heure où quelqu'un travaille dessus.
> Une ressource allumée « pour une personne » coûte autant que pour six.

## 1. Où travailler

| Activité | Où | Coût |
|---|---|---|
| Écrire et tester son code | **local** (`docker compose`) | 0 |
| Vérifier son Terraform | `terraform validate` + `plan` de la CI | 0 |
| Intégration de bout en bout | **session cloud commune** (1 soir / semaine) | quelques DH |
| Démo | apply le matin, destroy après | quelques DH |

## 2. SKU choisis en dev

| Service | Choix | Pourquoi |
|---|---|---|
| API Gateway, SQS, Lambda | paiement à l'usage | quasi gratuit à notre volume |
| DynamoDB | on-demand | aucun coût fixe |
| Container Apps | Consumption, `min_replicas = 0` | échelle à zéro + crédit mensuel gratuit |
| Service Bus | **Basic** | files seulement, centimes ; Standard (≈ 10 $/mois) inutile ici |
| Cosmos DB | **free tier** 1000 RU/s partagés | 0 ; un seul compte free tier par abonnement |
| Blob Storage | LRS, Hot | centimes |
| Static Web Apps | **Free** (Standard ≈ 9 $/mois seulement la semaine de la démo) | |
| Key Vault | Standard | centimes |
| Log Analytics | plafond journalier 0,2 Go, rétention 30 j | sous la franchise gratuite |
| Registre d'images | **GHCR** (gratuit, dépôt public) au lieu d'Azure Container Registry | ACR Basic ≈ 5 $/mois |

## 3. Garde-fous à poser le premier jour

- **Budget Azure** : Cost Management → Budgets → 10 $ / mois, alertes à 50 %, 80 %, 100 % à toute l'équipe.
- **Budget AWS** : Billing → Budgets → modèle « Zero spend » + budget 5 $.
- **Tags** `project=foodaid`, `env=dev` sur toutes les ressources (ajoutés par Terraform) : la facture se filtre par projet.

## 4. Créer puis détruire

1. Début de session : **Actions → terraform-apply**.
2. Tests de bout en bout.
3. Fin de session : **Actions → terraform-destroy** (`DETRUIRE`).

Restent en permanence (gratuits ou quasi) : le stockage du state Terraform, l'App registration Entra ID, le paramètre SSM.

## 5. Avant de partir

```bash
az resource list -g rg-foodaid-dev -o table                                  # doit être vide après un destroy
aws resourcegroupstaggingapi get-resources --tag-filters Key=project,Values=foodaid --query "ResourceTagMappingList[].ResourceARN"
```
