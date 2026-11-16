## Quoi ?

<!-- En une ou deux phrases : ce que cette PR ajoute ou corrige. -->

## Partie concernée

- [ ] Étudiant 1 · Ingestion
- [ ] Étudiant 2 · Validation des lots
- [ ] Étudiant 3 · Calcul
- [ ] Étudiant 4 · Données
- [ ] Étudiant 5 · Accès
- [ ] Étudiant 6 · Sécurité
- [ ] Partagé (contrats, Terraform racine, CI)

## Vérifications

- [ ] testé en local (`docker compose -f local/docker-compose.yml up`)
- [ ] tests ajoutés / mis à jour
- [ ] aucun secret, mot de passe ou fichier `.env` dans les fichiers modifiés
- [ ] si `contracts/` change : les étudiants concernés sont relecteurs
- [ ] si `infra/` change : le `terraform plan` de la CI a été lu (rien de supprimé par erreur)
