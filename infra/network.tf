# infra/network.tf

resource "azurerm_virtual_network" "vnet" {
  name                = "pfa-vnet"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  address_space       = ["10.0.0.0/16"]

  tags = {
    environment = "Development"
    project     = "Personal Finance App"
  }
}

resource "azurerm_subnet" "default" {
  name                 = "default-subnet"
  resource_group_name  = module.resource_group.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}