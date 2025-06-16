# infra/jobs.tf

resource "azurerm_container_app_job" "migration_job" {
  name                         = "pfa-migration-job"
  location                     = module.resource_group.location
  resource_group_name          = module.resource_group.name
  container_app_environment_id = azurerm_container_app_environment.aca_env.id

  replica_timeout_in_seconds = 300 # Give the job 5 minutes to complete
  replica_retry_limit        = 1
  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }

  template {
    container {
      name    = "migration-container"
      image   = var.docker_image_to_deploy
      cpu     = 0.25
      memory  = "0.5Gi"
      command = ["flask", "--app", "run:app", "db", "upgrade"]

      # The job needs the same environment variables as the main app to connect to the DB
      env {
        name        = "FLASK_APP"
        value       = "run:app" # Tells flask which app object to use
      }
      env {
        name        = "SECRET_KEY" # This is good to have for consistency
        secret_name = "flask-secret-key"
      }
      env {
        name        = "DB_HOST" # CORRECTED NAME
        value       = azurerm_mssql_server.pfa_sql_server.fully_qualified_domain_name
      }
      env {
        name        = "DB_NAME" # This was correct
        value       = azurerm_mssql_database.pfa_db_free.name
      }
      env {
        name        = "DB_USER" # CORRECTED NAME
        secret_name = "db-admin-login"
      }
      env {
        name        = "DB_PASSWORD" # CORRECTED NAME
        secret_name = "db-password"
      }
    }
  }

  # The job needs the same secrets as the main app
  secret {
    name  = "flask-secret-key"
    value = var.flask_secret_key
  }
  secret {
    name  = "recurring-job-secret"
    value = var.task_secret_key
  }
  secret {
    name  = "db-admin-login"
    value = var.db_admin_login
  }
  secret {
    name  = "db-password"
    value = var.db_admin_password
  }
}