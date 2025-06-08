# infra/database.tf

# This data source gets your current public IP address.
# We use a service that specifically returns the IPv4 address.
# data "http" "myip" {
#   url = "https://ipv4.icanhazip.com"
# }

# Generates a random string to ensure the SQL server name is globally unique.
resource "random_string" "unique" {
  length  = 6
  special = false
  upper   = false
}

# --- Azure SQL Server (Logical Server) ---
resource "azurerm_mssql_server" "sql_server" {
  name                         = "pfa-sql-server-${random_string.unique.result}"
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = var.db_admin_login
  administrator_login_password = var.db_admin_password

  public_network_access_enabled = true
}

# --- Azure SQL Database ---
resource "azurerm_mssql_database" "sql_database" {
  name      = "finance_db"
  server_id = azurerm_mssql_server.sql_server.id
  sku_name  = "Basic"
}

# --- Azure SQL Firewall Rules ---
# resource "azurerm_mssql_firewall_rule" "local_access" {
#   name             = "AllowMyIP"
#   server_id        = azurerm_mssql_server.sql_server.id
#   start_ip_address = chomp(data.http.myip.response_body)
#   end_ip_address   = chomp(data.http.myip.response_body)
# }

resource "azurerm_mssql_firewall_rule" "azure_access" {
  name             = "AllowAllWindowsAzureIps"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}