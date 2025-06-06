# infra/main.tf

# --- 1. Terraform and Provider Configuration ---
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# --- 2. Resource Definition ---
# This resource group now uses variables for its name and location.
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}