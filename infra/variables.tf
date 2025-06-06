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