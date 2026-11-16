output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.main.id
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "hmac_secret_versionless_id" {
  value = "${azurerm_key_vault.main.vault_uri}secrets/hmac-ingest-key"
}
