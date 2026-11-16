variable "region" {
  type    = string
  default = "eu-west-3" # Paris
}

variable "env" {
  type    = string
  default = "dev"
}

variable "azure_ingest_url" {
  description = "URL de POST /ingest sur Azure (sortie de la stack Azure : api_url + /ingest)"
  type        = string
  default     = "https://example.invalid/ingest"
}

variable "hmac_ssm_param" {
  description = "Nom du paramètre SSM SecureString contenant la clé HMAC (créé à la main par l'Étudiant 6, jamais dans Terraform)"
  type        = string
  default     = "/foodaid/hmac-ingest-key"
}
