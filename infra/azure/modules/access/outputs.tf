output "default_hostname" {
  value = azurerm_static_web_app.portal.default_host_name
}

output "deployment_token" {
  value     = azurerm_static_web_app.portal.api_key
  sensitive = true
}
