# infra/modules/resource_group/variables.tf

variable "rg_name" {
  type        = string
  description = "The name for the Azure Resource Group."
}

variable "location" {
  type        = string
  description = "The Azure region for the Resource Group."
}