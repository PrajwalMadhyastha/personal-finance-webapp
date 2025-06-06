# infra/outputs.tf

output "resource_group_name" {
  description = "The name of the created resource group."
  value       = azurerm_resource_group.rg.name
}

output "resource_group_id" {
  description = "The unique ID of the created resource group."
  value       = azurerm_resource_group.rg.id
}

output "postgresql_server_name" {
  description = "The name of the PostgreSQL flexible server."
  value       = azurerm_postgresql_flexible_server.pg_server.name
}

output "postgresql_server_fqdn" {
  description = "The fully qualified domain name of the PostgreSQL server."
  value       = azurerm_postgresql_flexible_server.pg_server.fqdn
}