# infra/database.tf

# This resource generates a random string to ensure the server name is globally unique.
resource "random_string" "unique" {
  length  = 6
  special = false
  upper   = false
}

# --- Azure PostgreSQL Flexible Server ---
resource "azurerm_postgresql_flexible_server" "pg_server" {
  name                = "pfa-postgres-server-${random_string.unique.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  version             = "14"                      # Specify a PostgreSQL version
  delegated_subnet_id = azurerm_subnet.default.id # Deploy into our existing subnet

  administrator_login    = var.db_admin_login
  administrator_password = var.db_admin_password

  zone = "1" # Deploy to availability zone 1

  # For a learning project, the smallest Burstable SKU is cost-effective.
  sku_name = "B_Standard_B1ms"

  storage_mb = 32768 # Minimum storage size (32 GB)

  # Disable public access for security. We will access it from within the VNet.
  public_network_access_enabled = false

  tags = {
    environment = "Development"
    project     = "Personal Finance App"
  }
}

# --- Azure PostgreSQL Database within the Server ---
resource "azurerm_postgresql_flexible_server_database" "pg_database" {
  name      = "finance_db"
  server_id = azurerm_postgresql_flexible_server.pg_server.id
  charset   = "UTF8"
}