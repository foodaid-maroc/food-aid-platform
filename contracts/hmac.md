# Signature HMAC entre AWS et Azure

La Lambda (AWS) signe chaque lot ; l'API (Azure) refuse tout lot mal signé, trop vieux ou rejoué.

## En-têtes envoyés par la Lambda

| En-tête | Valeur |
|---|---|
| `Content-Type` | `application/json` |
| `X-Timestamp` | heure d'envoi, secondes Unix (ex. `1794700000`) |
| `X-Nonce` | UUID v4 unique par envoi |
| `X-Signature` | `sha256=<hex>` |

## Calcul de la signature

```
message   = X-Timestamp + "." + X-Nonce + "." + corps_brut_en_octets
signature = HMAC-SHA256(clé_partagée, message)  → hexadécimal minuscule
```

- Le **corps brut** est signé tel quel (pas de re-sérialisation JSON côté API).
- La comparaison côté API se fait en **temps constant** (`hmac.compare_digest`).

## Règles de rejet côté API (`401`)

1. signature absente ou différente ;
2. `|maintenant − X-Timestamp| > 300 s` (fenêtre de 5 minutes) ;
3. `X-Nonce` déjà vu dans la fenêtre (anti-rejeu).

## La clé partagée

- Nom : `hmac-ingest-key` dans **Key Vault** (Étudiant 6).
- Côté AWS : copie dans **SSM Parameter Store (SecureString)** `/foodaid/hmac-ingest-key`, lue par la Lambda.
- En local : `dev-secret-change-me` (valeur publique, uniquement pour les émulateurs).

Exemple de référence (pour tester vos implémentations) : clé `dev-secret-change-me`, timestamp `1794700000`, nonce `00000000-0000-4000-8000-000000000000`, corps `{"a":1}` → la signature doit être identique en Python et en Node.
