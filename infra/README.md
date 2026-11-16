# Infrastructure (Terraform)

| Dossier | Contenu | Qui l'applique |
|---|---|---|
| `bootstrap/` | stockage du **state distant** (Azure Storage) — une seule fois | propriétaire de l'abonnement, depuis son PC |
| `azure/` | stack Azure : `modules/compute`, `data`, `access`, `security` | **GitHub Actions uniquement** |
| `aws/` | stack AWS : `modules/ingest`, `logic` | **GitHub Actions uniquement** |

Chaque étudiant travaille dans **son** module. Les deux stacks ont chacune leur state (`azure.tfstate`, `aws.tfstate`), **verrouillé** pendant un `plan`/`apply` : deux exécutions simultanées ne peuvent pas se corrompre.

## Vérifier son code sans compte cloud

```bash
cd infra/azure            # ou infra/aws
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

## Cycle de vie

1. PR → la CI lance `fmt`, `validate`, puis `plan` (aucune ressource créée).
2. Session d'intégration → **Actions → terraform-apply** (validation humaine requise).
3. Fin de session → **Actions → terraform-destroy** (taper `DETRUIRE`).

L'ordre est géré par le pipeline : Azure d'abord (l'URL de l'API est nécessaire à la Lambda), AWS ensuite ; destruction dans l'ordre inverse.
