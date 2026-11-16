output "api_url" {
  value = module.compute.api_url
}

output "portal_url" {
  value = "https://${module.access.default_hostname}"
}

output "key_vault_name" {
  value = module.security.key_vault_name
}
