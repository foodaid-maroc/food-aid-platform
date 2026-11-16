terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.20" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }
  # State dans Azure Storage (verrouillé). Valeurs passées par la CI : -backend-config=...
  backend "azurerm" {}
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true # permet de recréer le coffre après un destroy
    }
  }
}
