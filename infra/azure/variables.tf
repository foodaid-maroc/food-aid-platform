variable "location" {
  type    = string
  default = "swedencentral" # région autorisée par la policy Azure for Students (vérifier avec az policy assignment list)
}

variable "swa_location" {
  description = "Static Web Apps n'existe que dans quelques régions (westeurope, eastus2, centralus, westus2, eastasia)"
  type        = string
  default     = "westeurope"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "api_image" {
  description = "Image publique GHCR de l'app api (construite par le workflow images)"
  type        = string
  default     = "mcr.microsoft.com/k8se/quickstart:latest"
}

variable "workers_image" {
  type    = string
  default = "mcr.microsoft.com/k8se/quickstart:latest"
}

variable "entra_tenant_id" {
  type    = string
  default = ""
}

variable "entra_api_audience" {
  description = "ex. api://<client-id> (App registration du portail, Étudiant 5)"
  type        = string
  default     = ""
}

variable "log_daily_quota_gb" {
  description = "Plafond journalier Log Analytics : garde-fou contre les coûts"
  type        = number
  default     = 0.2
}
