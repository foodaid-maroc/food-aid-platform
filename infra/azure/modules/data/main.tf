# Étudiant 4 · Cosmos DB (free tier) + Blob Storage
resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-foodaid-${var.suffix}"
  resource_group_name = var.rg_name
  location            = var.location
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  tags                = var.tags

  free_tier_enabled             = true # 1000 RU/s + 25 Go gratuits (un seul compte free tier par abonnement)
  local_authentication_disabled = true # pas de clés : identité managée uniquement

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }
}

resource "azurerm_cosmosdb_sql_database" "foodaid" {
  name                = "foodaid"
  resource_group_name = var.rg_name
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = 1000 # débit partagé entre les conteneurs = exactement le free tier
}

resource "azurerm_cosmosdb_sql_container" "stock" {
  name                = "stock"
  resource_group_name = var.rg_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.foodaid.name
  partition_key_paths = ["/partnerId"]
}

resource "azurerm_cosmosdb_sql_container" "alerts" {
  name                = "alerts"
  resource_group_name = var.rg_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.foodaid.name
  partition_key_paths = ["/partnerId"]
}

resource "azurerm_cosmosdb_sql_container" "nonces" {
  name                = "nonces"
  resource_group_name = var.rg_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.foodaid.name
  partition_key_paths = ["/id"]
  default_ttl         = -1 # TTL activé ; chaque nonce porte "ttl": 600
}

# Rôle de données Cosmos « Built-in Data Contributor » pour l'identité des apps
resource "azurerm_cosmosdb_sql_role_assignment" "apps" {
  resource_group_name = var.rg_name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = "${azurerm_cosmosdb_account.main.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = var.apps_principal_id
  scope               = azurerm_cosmosdb_account.main.id
}

resource "azurerm_storage_account" "main" {
  name                            = "stfoodaid${var.suffix}"
  resource_group_name             = var.rg_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = var.tags
}

resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "exports" {
  name                  = "exports"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_role_assignment" "apps_blob" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.apps_principal_id
}
