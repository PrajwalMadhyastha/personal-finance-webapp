# infra/container_app.tf (Final Corrected Version)

resource "azurerm_container_app" "webapp" {
  name                         = "pfa-webapp"
  container_app_environment_id = azurerm_container_app_environment.aca_env.id
  resource_group_name          = module.resource_group.name
  revision_mode                = "Single"

  # --- SECRET DEFINITION BLOCK ---
  # This block defines all the secrets the app can use.
  # We must define 'flask-secret-key' and all others here.
  secret {
    name  = "flask-secret-key"
    value = var.flask_secret_key
  }
  secret {
    name  = "recurring-job-secret"
    value = var.task_secret_key
  }
  secret {
    name  = "ghcr-pat"
    value = var.github_pat
  }
  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.pfa_storage.primary_connection_string
  }
  # --- END OF SECRET DEFINITION BLOCK ---

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

      # --- ENVIRONMENT VARIABLE BLOCK ---
      # This block correctly uses the secrets defined above.
      env {
        name  = "DATABASE_URL"
        value = "mssql+pyodbc://${var.db_admin_login}:${urlencode(var.db_admin_password)}@${azurerm_mssql_server.pfa_sql_server.fully_qualified_domain_name}:1433/${azurerm_mssql_database.pfa_db_free.name}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&ConnectionTimeout=30"
      }
      env {
        name  = "FLASK_APP"
        value = "run:app"
      }
      env {
        name        = "SECRET_KEY"
        secret_name = "flask-secret-key"
      }
      env {
        name        = "TASK_SECRET_KEY"
        secret_name = "recurring-job-secret"
      }
      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }
    }
  }
}