# infra/main.tf

# --- 1. Terraform and Provider Configuration ---
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.0"
}

provider "azurerm" {
  features {}
}

# --- 2. Resource Definition ---
module "resource_group" {
  source = "./modules/resource_group"

  # Pass values from your root variables.tf into the module's variables
  rg_name  = var.resource_group_name
  location = var.location
}

moved {
  from = azurerm_resource_group.rg
  to   = module.resource_group.azurerm_resource_group.this
}