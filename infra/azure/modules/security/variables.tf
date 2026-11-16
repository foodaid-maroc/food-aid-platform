variable "rg_name" { type = string }
variable "location" { type = string }
variable "suffix" { type = string }
variable "tags" { type = map(string) }
variable "tenant_id" { type = string }
variable "apps_principal_id" { type = string }
variable "log_daily_quota_gb" { type = number }
