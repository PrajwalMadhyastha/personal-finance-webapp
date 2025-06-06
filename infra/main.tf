# --- 1. Terraform and Provider Configuration ---
# This block configures Terraform itself and the required providers.
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0" # Use a recent version of the Azure provider
    }
  }
}

# Configure the Azure Provider.
# It will automatically use the credentials from your 'az login'.
provider "azurerm" {
  features {}
}

# --- 2. Resource Definition ---
# This block defines the Azure Resource Group we want to create.
resource "azurerm_resource_group" "rg" {
  # The name of the resource group in Azure.
  name = "personal-finance-app-rg"

  # The Azure region where the resource group will be created.
  location = "Central India"
}