# infra/outputs.tf

output "resource_group_name" {
  description = "The name of the created resource group."
  value       = azurerm_resource_group.rg.name
}

output "resource_group_id" {
  description = "The unique ID of the created resource group."
  value       = azurerm_resource_group.rg.id
}