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

# infra/variables.tf

variable "db_admin_login" {
  type        = string
  description = "The admin username for the PostgreSQL server."
  sensitive   = true # Marks the variable as sensitive in logs/outputs
}

variable "db_admin_password" {
  type        = string
  description = "The admin password for the PostgreSQL server."
  sensitive   = true
}

variable "github_username" {
  type        = string
  description = "Your GitHub username for pulling images from GHCR."
}

variable "github_pat" {
  type        = string
  description = "A GitHub PAT with read:packages scope to pull the container image."
  sensitive   = true # This prevents Terraform from showing the PAT in logs
}