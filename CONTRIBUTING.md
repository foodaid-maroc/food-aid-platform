# Contribuer

## 1. Une branche par tâche

```bash
git checkout main && git pull
git checkout -b etudiant5/portail-connexion      # <etudiantN>/<tâche-courte>
```

## 2. Commits clairs

Format : `type(zone): message`

| type | quand |
|---|---|
| `feat` | nouvelle fonctionnalité |
| `fix` | correction |
| `infra` | Terraform |
| `ci` | GitHub Actions |
| `docs` | documentation |
| `contract` | changement dans `contracts/` |

Exemples : `feat(portal): page Partenaire`, `infra(data): conteneur Cosmos stock`, `contract(lot): ajout du champ expiryDate`.

## 3. Pull Request

```bash
git push -u origin etudiant5/portail-connexion
```

Puis ouvrir une PR vers `main` sur GitHub :

- remplir le modèle de PR ;
- la CI doit être **verte** (tests, build, `terraform fmt/validate`, `terraform plan`) ;
- **1 approbation minimum** ; le propriétaire du dossier est ajouté automatiquement (`CODEOWNERS`) ;
- fusion en **Squash and merge**.

## 4. Changer un contrat

Un fichier de `contracts/` est utilisé par plusieurs étudiants : toute modification passe par une PR `contract(...)` **approuvée par les étudiants concernés** avant que chacun adapte son code.

## 5. Ce qu'on ne commit jamais

- fichiers `.env`, `local.settings.json`, `*.tfvars` contenant des valeurs réelles ;
- clés, mots de passe, chaînes de connexion, jetons ;
- dossiers `node_modules/`, `.terraform/`, `__pycache__/`.

Un secret commité par erreur doit être **considéré comme compromis** : prévenir l'Étudiant 6 et le régénérer.
