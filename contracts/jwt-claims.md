# Jeton (JWT) et rôles

Entra ID authentifie l'utilisateur ; le portail envoie le jeton à `GET /query` ; l'API applique le **RBAC**.

## App roles (App registration `foodaid-portal`)

| Valeur exacte du rôle | Qui | Voit |
|---|---|---|
| `Staff` | personnel de la Banque Alimentaire | tout le stock, toutes les livraisons |
| `Partner` | association / entrepôt partenaire | **uniquement** ses données (`partnerId`) |
| `Donor` | donateur | l'impact agrégé de ses dons |
| `Auditor` | auditeur | tout, **lecture seule**, + copies brutes |

## Claims utilisés par l'API

| Claim | Exemple | Usage |
|---|---|---|
| `roles` | `["Partner"]` | décide quelles données renvoyer |
| `oid` | identifiant Entra de l'utilisateur | traçabilité dans les logs |
| `partnerId` | `P2` | filtre et **clé de partition** Cosmos pour le rôle Partner |

`partnerId` n'existe pas par défaut dans Entra ID : l'Étudiant 5 l'ajoute comme **claim optionnel / attribut d'extension**, ou à défaut l'API le déduit d'une table `users → partnerId` dans Cosmos.

## En local

L'API accepte un rôle simulé (uniquement si `AUTH_MODE=dev`) :

```
X-Dev-Role: Partner
X-Dev-Partner: P2
```

En production, `AUTH_MODE=entra` : seul un JWT valide (signature, `aud`, `iss`, expiration) est accepté.
