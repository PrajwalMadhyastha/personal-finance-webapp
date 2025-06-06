# infra/network.tf

# Define a Virtual Network (VNet) within our resource group
resource "azurerm_virtual_network" "vnet" {
  name                = "pfa-vnet" # pfa = personal-finance-app
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]

  tags = {
    environment = "Development"
    project     = "Personal Finance App"
  }
}

# Define a Subnet within the VNet
resource "azurerm_subnet" "default" {
  name                 = "default-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}