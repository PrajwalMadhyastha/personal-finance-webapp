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

  # We only need one secret now: the DB password
  secret {
    name  = "db-password"
    value = var.db_admin_password
  }

  template {
    container {
      name   = "migration-container"
      image  = var.docker_image_to_deploy
      cpu    = 0.25
      memory = "0.5Gi"

      # This is the new, robust command. It constructs the full URI and passes it.
      command = [
        "python",
        "scripts/run_migrations.py",
        "mssql+pyodbc://${var.db_admin_login}:${secret.db-password}@${azurerm_mssql_server.pfa_sql_server.fully_qualified_domain_name}:1433/${azurerm_mssql_database.pfa_db_free.name}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&ConnectionTimeout=30"
      ]
    }
  }
}