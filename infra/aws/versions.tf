terraform {
  required_version = ">= 1.6"
  required_providers {
    aws     = { source = "hashicorp/aws", version = ">= 5.70, < 7.0" }
    archive = { source = "hashicorp/archive", version = "~> 2.6" }
  }
  # State dans Azure Storage (verrouillé). Valeurs passées par la CI : -backend-config=...
  backend "azurerm" {}
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { project = "foodaid", env = var.env, managed_by = "terraform" }
  }
}
