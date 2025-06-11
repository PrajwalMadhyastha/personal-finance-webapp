# infra/backend.tf

terraform {
  backend "azurerm" {
    # Replace these names with the ones you used in the 'az' commands above
    resource_group_name  = "tfstate-rg"
    storage_account_name = "pfatfstatefinanceapp"
    container_name       = "tfstate"
    # This will be the name of the state file inside the container
    key = "prod.terraform.tfstate"
  }
}