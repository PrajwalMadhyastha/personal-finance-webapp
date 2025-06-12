# infra/variables.tf

variable "resource_group_name" {
  type        = string
  description = "The name of the Azure Resource Group."
  default     = "personal-finance-app-rg"
}

variable "location" {
  type        = string
  description = "The Azure region where resources will be deployed."
  default     = "Central India"
}

variable "db_admin_login" {
  type        = string
  description = "The admin username for the SQL server."
  sensitive   = true
}

variable "db_admin_password" {
  type        = string
  description = "The admin password for the SQL server."
  sensitive   = true
}

# This variable will be provided by the CI/CD pipeline
variable "docker_image_to_deploy" {
  type        = string
  description = "The full, specific Docker image tag to deploy (e.g., ghcr.io/owner/repo:sha)."
}

# These variables are for GHCR authentication
variable "github_username" {
  type        = string
  description = "Your GitHub username for pulling images from GHCR."
}

variable "github_pat" {
  type        = string
  description = "A GitHub PAT with read:packages scope to pull the container image."
  sensitive   = true
}

variable "flask_secret_key" {
  description = "The secret key used by Flask for session signing."
  type        = string
  sensitive   = true # Marks this as a sensitive value
}