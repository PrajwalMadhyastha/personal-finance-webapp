# infra/jobs.tf (Final Corrected Version)

resource "azurerm_container_app_job" "migration_job" {
  name                         = "pfa-migration-job"
  location                     = module.resource_group.location
  resource_group_name          = module.resource_group.name
  container_app_environment_id = azurerm_container_app_environment.aca_env.id

  replica_timeout_in_seconds = 300
  replica_retry_limit        = 1
  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }

  # Define ALL configuration items as secrets
  secret {
    name  = "flask-secret-key"
    value = var.flask_secret_key
  }
  secret {
    name  = "db-admin-login"
    value = var.db_admin_login
  }
  secret {
    name  = "db-password"
    value = var.db_admin_password
  }
  # --- NEW SECRETS for host and name ---
  secret {
    name  = "db-host"
    value = azurerm_mssql_server.pfa_sql_server.fully_qualified_domain_name
  }
  secret {
    name  = "db-name"
    value = azurerm_mssql_database.pfa_db_free.name
  }


  template {
    container {
      name    = "migration-container"
      image   = var.docker_image_to_deploy
      cpu     = 0.25
      memory  = "0.5Gi"
      # IMPORTANT: Remember to change this back after testing!
      command = ["sh", "-c", "printenv | sort"] # Keep this for one more test run

      # Now, reference EVERYTHING as a secret
      env {
        name  = "FLASK_APP"
        value = "run:app"
      }
      env {
        name        = "SECRET_KEY"
        secret_name = "flask-secret-key"
      }
      env {
        name        = "DB_HOST"
        secret_name = "db-host" # Reference the new secret
      }
      env {
        name        = "DB_NAME"
        secret_name = "db-name" # Reference the new secret
      }
      env {
        name        = "DB_USER"
        secret_name = "db-admin-login"
      }
      env {
        name        = "DB_PASSWORD"
        secret_name = "db-password"
      }
    }
  }
}