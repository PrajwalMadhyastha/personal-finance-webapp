# infra/modules/resource_group/main.tf

resource "azurerm_resource_group" "this" {
  name     = var.rg_name
  location = var.location
}