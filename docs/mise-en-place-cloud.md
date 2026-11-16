# Mise en place cloud (une seule fois)

Principe : **un seul abonnement Azure, un seul compte AWS**, partagés par l'équipe. Les déploiements passent par GitHub Actions en **OIDC** (jetons temporaires) : aucune clé cloud n'est stockée dans GitHub ni sur les PC.

## Azure

### 1. Abonnement

Un membre fournit son abonnement **Azure for Students** (crédit 100 $, pas de carte bancaire).
Vérifier les régions autorisées par la policy (la valeur par défaut `swedencentral` en fait normalement partie) :

```bash
az policy assignment list --query "[?name=='sys.regionrestriction'].parameters.listOfAllowedLocations.value[]" -o tsv
```

### 2. State Terraform (propriétaire, depuis son PC)

```bash
az login
cd infra/bootstrap
terraform init && terraform apply
terraform output backend_config      # → variables GitHub TF_STATE_RG / TF_STATE_ACCOUNT / TF_STATE_CONTAINER
```

### 3. Identité de déploiement GitHub (OIDC)

```bash
SUB=$(az account show --query id -o tsv)
APP=$(az ad app create --display-name foodaid-github-deploy --query appId -o tsv)
az ad sp create --id $APP
# Droits : l'abonnement (création du groupe de ressources + attribution des rôles aux identités managées)
az role assignment create --assignee $APP --role Contributor --scope /subscriptions/$SUB
az role assignment create --assignee $APP --role "Role Based Access Control Administrator" --scope /subscriptions/$SUB
# Accès au state
az role assignment create --assignee $APP --role "Storage Blob Data Contributor" \
  --scope $(az storage account show -n <TF_STATE_ACCOUNT> --query id -o tsv)
# Confiance GitHub : branche main + environnement dev + PR
for SUBJ in "repo:<organisation>/food-aid-platform:environment:dev" "repo:<organisation>/food-aid-platform:pull_request"; do
  az ad app federated-credential create --id $APP --parameters "{\"name\":\"$(echo $SUBJ | tr ':/' '--')\",\"issuer\":\"https://token.actions.githubusercontent.com\",\"subject\":\"$SUBJ\",\"audiences\":[\"api://AzureADTokenExchange\"]}"
done
echo "AZURE_CLIENT_ID=$APP  AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)  AZURE_SUBSCRIPTION_ID=$SUB"
```

> Si le tenant de l'école interdit `az ad app create`, le propriétaire crée un **service principal avec secret** à la place et le stocke en secret GitHub (solution de repli, moins propre).

### 4. Accès des membres (portail, lecture et tests)

Chaque membre reçoit **Reader** sur l'abonnement : il voit les ressources, les logs et les coûts, mais toute modification passe par Terraform (PR → pipeline) :

```bash
az role assignment create --assignee <email-esi-du-membre> --role Reader --scope /subscriptions/$SUB
```

### 5. Clé HMAC (Étudiant 6, après le premier apply)

```bash
KEY=$(openssl rand -hex 32)
az keyvault secret set --vault-name <kv-foodaid-xxxxx> --name hmac-ingest-key --value "$KEY"
aws ssm put-parameter --name /foodaid/hmac-ingest-key --type SecureString --value "$KEY" --overwrite
```

## AWS

### 1. Compte

Un seul compte AWS (Free plan : crédits offerts aux nouveaux comptes). **Activer la MFA sur le compte root** et ne plus l'utiliser.

### 2. Rôle de déploiement GitHub (OIDC)

IAM → **Identity providers** → Add → OpenID Connect : `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
IAM → **Roles** → Create → Web identity → ce fournisseur → condition `token.actions.githubusercontent.com:sub` = `repo:<organisation>/food-aid-platform:*` → politiques : `AmazonSQSFullAccess`, `AmazonAPIGatewayAdministrator`, `AWSLambda_FullAccess`, `AmazonDynamoDBFullAccess`, `CloudWatchFullAccessV2`, `IAMFullAccess` (à restreindre plus tard). Nom : `foodaid-github-deploy`.

### 3. Membres

IAM → **Users** : un utilisateur par membre, accès console, groupe `foodaid-dev` avec **ReadOnlyAccess** (consulter les logs, la file, la table). Les modifications passent par Terraform.

## Variables GitHub

**Organisation ou dépôt → Settings → Secrets and variables → Actions → Variables** :

| Variable | Valeur |
|---|---|
| `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` | étape Azure 3 |
| `TF_STATE_RG`, `TF_STATE_ACCOUNT`, `TF_STATE_CONTAINER` | étape Azure 2 |
| `AWS_ROLE_ARN` | ARN du rôle `foodaid-github-deploy` |
| `AWS_REGION` | `eu-west-3` |
| `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_API_SCOPE`, `ENTRA_API_AUDIENCE` | Étudiant 5 (App registration) |
| `API_URL`, `SWA_ENABLED` | après le premier apply (`terraform output`) |

Secret (et non variable) : `AZURE_STATIC_WEB_APPS_API_TOKEN` (portail Azure → Static Web App → Manage deployment token).
