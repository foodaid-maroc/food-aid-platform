data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

locals {
  suffix = random_string.suffix.result
  tags   = { project = "foodaid", env = var.env, managed_by = "terraform" }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-foodaid-${var.env}"
  location = var.location
  tags     = local.tags
}

# Identité managée partagée par les apps : on lui donne les droits AVANT de créer les apps
resource "azurerm_user_assigned_identity" "apps" {
  name                = "id-foodaid-apps-${var.env}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

# Étudiant 6
module "security" {
  source             = "./modules/security"
  rg_name            = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  suffix             = local.suffix
  tags               = local.tags
  tenant_id          = data.azurerm_client_config.current.tenant_id
  apps_principal_id  = azurerm_user_assigned_identity.apps.principal_id
  log_daily_quota_gb = var.log_daily_quota_gb
}

# Étudiant 4
module "data" {
  source            = "./modules/data"
  rg_name           = azurerm_resource_group.main.name
  location          = azurerm_resource_group.main.location
  suffix            = local.suffix
  tags              = local.tags
  apps_principal_id = azurerm_user_assigned_identity.apps.principal_id
}

# Étudiant 3
module "compute" {
  source                     = "./modules/compute"
  rg_name                    = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  suffix                     = local.suffix
  tags                       = local.tags
  identity_id                = azurerm_user_assigned_identity.apps.id
  identity_client_id         = azurerm_user_assigned_identity.apps.client_id
  apps_principal_id          = azurerm_user_assigned_identity.apps.principal_id
  log_analytics_workspace_id = module.security.log_analytics_workspace_id
  hmac_secret_id             = module.security.hmac_secret_versionless_id
  cosmos_endpoint            = module.data.cosmos_endpoint
  blob_account_url           = module.data.blob_account_url
  api_image                  = var.api_image
  workers_image              = var.workers_image
  entra_tenant_id            = var.entra_tenant_id
  entra_api_audience         = var.entra_api_audience
  allowed_origin             = "https://${module.access.default_hostname}"
}

# Étudiant 5
module "access" {
  source   = "./modules/access"
  rg_name  = azurerm_resource_group.main.name
  location = var.swa_location
  suffix   = local.suffix
  tags     = local.tags
}
