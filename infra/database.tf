# --- Azure SQL Server ---
# This block is correct as you've defined it.
resource "azurerm_mssql_server" "pfa_sql_server" {
  name                          = "pfa-sql-server-kpm477"
  resource_group_name           = module.resource_group.name
  location                      = module.resource_group.location
  version                       = "12.0"
  administrator_login           = var.db_admin_login
  administrator_login_password  = var.db_admin_password
  public_network_access_enabled = true
}

# --- Azure SQL Firewall Rules ---
resource "azurerm_mssql_firewall_rule" "azure_access" {
  name = "AllowAllWindowsAzureIps"
  # FIXED: This now correctly points to the renamed server resource.
  server_id        = azurerm_mssql_server.pfa_sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_mssql_firewall_rule" "dev_ip_range_access" {
  name = "AllowDevIPRange"
  # FIXED: This now correctly points to the renamed server resource.
  server_id        = azurerm_mssql_server.pfa_sql_server.id
  start_ip_address = "223.185.0.0" # Note: This is a very wide range.
  end_ip_address   = "223.185.255.255"
}

# --- New Free Azure SQL Database ---
# This block is correct as you've defined it.
resource "azurerm_mssql_database" "pfa_db_free" {
  name                        = "finance_db_new"
  server_id                   = azurerm_mssql_server.pfa_sql_server.id
  sku_name                    = "GP_S_Gen5_2"
  min_capacity                = 0.5
  auto_pause_delay_in_minutes = 60
  storage_account_type        = "Local"
  max_size_gb                 = 32
  zone_redundant              = false
}