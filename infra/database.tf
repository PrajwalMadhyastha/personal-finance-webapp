
# infra/database.tf
# NOTE: The 'data "http" "myip"' and 'local_access' firewall rule have been removed as per our previous discussion.
resource "random_string" "unique" {
  length  = 6
  special = false
  upper   = false
}
# --- Azure SQL Server ---
resource "azurerm_mssql_server" "sql_server" {
  name                          = "pfa-sql-server-${random_string.unique.result}"
  resource_group_name           = module.resource_group.name
  location                      = module.resource_group.location
  version                       = "12.0"
  administrator_login           = var.db_admin_login
  administrator_login_password  = var.db_admin_password
  public_network_access_enabled = true
}
# --- Azure SQL Database ---
resource "azurerm_mssql_database" "sql_database" {
  name                        = "finance_db"
  server_id                   = azurerm_mssql_server.sql_server.id
  sku_name                    = "GP_S_Gen5_1"
  auto_pause_delay_in_minutes = 60
  min_capacity                = 0.5
  max_size_gb                 = 32
}
# --- Azure SQL Firewall Rule for Azure Services ---
resource "azurerm_mssql_firewall_rule" "azure_access" {
  name             = "AllowAllWindowsAzureIps"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_mssql_firewall_rule" "dev_ip_range_access" {
  name             = "AllowDevIPRange"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "223.185.0.0"
  end_ip_address   = "223.185.255.255"
}
