resource "azurerm_log_analytics_workspace" "logs" {
  name                = "pfa-log-analytics-workspace"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}