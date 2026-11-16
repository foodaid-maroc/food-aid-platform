# Étudiant 6 · Log Analytics + Key Vault
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-foodaid-${var.suffix}"
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = var.log_daily_quota_gb
  tags                = var.tags
}

resource "azurerm_key_vault" "main" {
  name                       = "kv-foodaid-${var.suffix}"
  resource_group_name        = var.rg_name
  location                   = var.location
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true # droits par RBAC, pas de politiques d'accès
  soft_delete_retention_days = 7
  purge_protection_enabled   = false # dev : permet destroy + recréation
  tags                       = var.tags
}

# Les apps peuvent LIRE les secrets, rien d'autre
resource "azurerm_role_assignment" "apps_read_secrets" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.apps_principal_id
}

# Journaux d'accès au coffre -> Log Analytics
resource "azurerm_monitor_diagnostic_setting" "kv" {
  name                       = "kv-to-law"
  target_resource_id         = azurerm_key_vault.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  enabled_log { category = "AuditEvent" }
}

# NB : la valeur du secret « hmac-ingest-key » n'est PAS dans Terraform (elle finirait dans le state).
# Elle est créée une fois par l'Étudiant 6 :
#   az keyvault secret set --vault-name <kv> --name hmac-ingest-key --value "<clé aléatoire>"
