# Mise en place GitHub (une seule fois, ~15 min)

Le dépôt est hébergé dans une **organisation d'équipe**, pas sur un compte personnel : chacun commit ses propres parties, et le dépôt n'affiche le pseudo de personne.

## 1. Créer l'organisation (un membre, le « propriétaire »)

1. https://github.com/account/organizations/new?plan=free → plan **Free**.
2. Nom proposé : `foodaid-maroc` (ou `esi-foodaid-<annee>` s'il est pris).
3. « This organization belongs to » → **My personal account**.

## 2. Inviter l'équipe

**Organisation → People → Invite member** : les 5 autres membres, rôle **Member**.
Facultatif : **Teams** → créer `etudiant-1` … `etudiant-6` (une équipe par partie) et les utiliser dans `CODEOWNERS`.

## 3. Créer le dépôt et pousser le squelette

1. **New repository** dans l'organisation : `food-aid-platform`, **Public**, sans README (il existe déjà).
2. Sur le PC du propriétaire, dans le dossier décompressé :

```bash
git init -b main
git add .
git commit -m "chore: squelette initial du projet"
git remote add origin https://github.com/<organisation>/food-aid-platform.git
git push -u origin main
```

## 4. Compléter `CODEOWNERS`

Dans `.github/CODEOWNERS`, remplacer chaque `@PSEUDO_ETUDIANT_N` par le pseudo GitHub du membre (ou `@<organisation>/etudiant-N`). Commit via une PR.

## 5. Protéger `main`

**Settings → Rules → Rulesets → New branch ruleset** :

| Réglage | Valeur |
|---|---|
| Target branches | `main` (Default branch) |
| Restrict deletions | ✓ |
| Block force pushes | ✓ |
| Require a pull request before merging | ✓ — 1 approbation, **Require review from Code Owners** |
| Require status checks to pass | ✓ — `secrets-scan` (les autres tests ne tournent que si leur dossier change) |

## 6. Environnement de déploiement

**Settings → Environments → New environment** `dev` → **Required reviewers** : 2 membres.
Ainsi, `terraform-apply` et `terraform-destroy` attendent une validation humaine.

## 7. Images publiques

Après le premier passage du workflow `images` : **Organisation → Packages** → `foodaid-api` et `foodaid-workers` → **Package settings → Change visibility → Public** (Container Apps les télécharge sans mot de passe).

## 8. Chaque membre

```bash
git clone https://github.com/<organisation>/food-aid-platform.git
cd food-aid-platform
git checkout -b etudiantN/ma-premiere-tache
```

Puis suivre le `README.md` (démarrage local) et `CONTRIBUTING.md`.
