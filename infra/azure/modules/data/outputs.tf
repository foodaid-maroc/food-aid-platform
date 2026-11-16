output "cosmos_endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "blob_account_url" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}
