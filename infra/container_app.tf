# infra/container_app.tf

resource "azurerm_container_app_environment" "aca_env" {
  name                       = "pfa-aca-environment"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}

resource "azurerm_container_app" "webapp" {
  name                         = "pfa-webapp"
  container_app_environment_id = azurerm_container_app_environment.aca_env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  secret {
    name  = "db-password"
    value = var.db_admin_password
  }
  secret {
    name  = "ghcr-pat"
    value = var.github_pat
  }

  ingress {
    external_enabled = true
    target_port      = 5000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
  registry {
    server               = "ghcr.io"
    username             = var.github_username
    password_secret_name = "ghcr-pat"
  }

  template {
    container {
      name   = "pfa-webapp-container"
      image  = "ghcr.io/${var.github_username}/personal-finance-webapp:main"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "DB_SERVER_FQDN"
        value = azurerm_mssql_server.sql_server.fully_qualified_domain_name
      }
      env {
        name  = "DB_NAME"
        value = azurerm_mssql_database.sql_database.name
      }
      env {
        name  = "DB_ADMIN_LOGIN"
        value = var.db_admin_login
      }
      env {
        name        = "DB_ADMIN_PASSWORD"
        secret_name = "db-password"
      }
      env {
        name  = "FLASK_DEBUG"
        value = "0"
      }
    }
  }
}