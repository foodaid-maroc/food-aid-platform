# À exécuter UNE SEULE FOIS par le propriétaire de l'abonnement Azure :
#   az login
#   terraform init && terraform apply
# Ce stockage n'est jamais détruit par le workflow « destroy » (il contient l'état de l'infra).
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.20" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "azurerm" {
  features {}
}

variable "location" {
  type    = string
  default = "swedencentral" # doit faire partie des régions autorisées par la policy Azure for Students
}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_resource_group" "tfstate" {
  name     = "rg-foodaid-tfstate"
  location = var.location
  tags     = { project = "foodaid", purpose = "terraform-state" }
}

resource "azurerm_storage_account" "tfstate" {
  name                            = "stfoodaidtf${random_string.suffix.result}"
  resource_group_name             = azurerm_resource_group.tfstate.name
  location                        = azurerm_resource_group.tfstate.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled = true # permet de récupérer un state écrasé par erreur
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"
}

output "backend_config" {
  description = "À copier dans les variables GitHub (Settings → Secrets and variables → Actions → Variables)"
  value = {
    TF_STATE_RG        = azurerm_resource_group.tfstate.name
    TF_STATE_ACCOUNT   = azurerm_storage_account.tfstate.name
    TF_STATE_CONTAINER = azurerm_storage_container.tfstate.name
  }
}
