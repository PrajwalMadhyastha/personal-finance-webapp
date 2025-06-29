# infra/outputs.tf

output "resource_group_name" {
  description = "The name of the created resource group."
  value       = module.resource_group.name
}

output "resource_group_id" {
  description = "The unique ID of the created resource group."
  value       = module.resource_group.id
}

# --- New Outputs for Azure SQL ---
output "sql_server_name" {
  description = "The name of the Azure SQL server."
  value       = azurerm_mssql_server.pfa_sql_server.name
}

output "sql_server_fqdn" {
  description = "The fully qualified domain name (FQDN) of the Azure SQL server."
  value       = azurerm_mssql_server.pfa_sql_server.fully_qualified_domain_name
}

output "sql_database_name" {
  description = "The name of the Azure SQL database."
  value       = azurerm_mssql_database.pfa_db_free.name
}

output "container_app_url" {
  description = "The FQDN of the deployed container app."
  value       = "https://${azurerm_container_app.webapp.name}.${azurerm_container_app_environment.aca_env.default_domain}"
}