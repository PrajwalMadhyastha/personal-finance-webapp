# In infra/container_app.tf

resource "azurerm_container_app" "webapp" {
  name                         = "pfa-webapp"
  container_app_environment_id = azurerm_container_app_environment.aca_env.id
  resource_group_name          = module.resource_group.name
  revision_mode                = "Single"

  # This secret definition block is correct.
  secret {
    name  = "db-admin-login"
    value = var.db_admin_login
  }
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
      image  = var.docker_image_to_deploy
      cpu    = 0.25
      memory = "0.5Gi"

      # --- THIS ENTIRE ENV BLOCK IS NOW CORRECT AND CONSISTENT ---
      env {
        name  = "DB_SERVER"
        value = azurerm_mssql_server.pfa_sql_server.fully_qualified_domain_name
      }
      env {
        name  = "DB_NAME"
        value = azurerm_mssql_database.pfa_db_free.name
      }
      env {
        name        = "DB_ADMIN_LOGIN"
        # FIXED: Securely references the secret instead of passing plain text.
        secret_name = "db-admin-login"
      }
      env {
        name        = "DB_ADMIN_PASSWORD"
        # This was already correct, referencing a secret.
        secret_name = "db-password"
      }
      env {
        # You may also want a secret for this in the future
        name  = "SECRET_KEY"
        value = var.flask_secret_key
      }
    }
  }
}

resource "azurerm_container_app_environment" "aca_env" {
  name                       = "pfa-aca-environment"
  location                   = module.resource_group.location
  resource_group_name        = module.resource_group.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}