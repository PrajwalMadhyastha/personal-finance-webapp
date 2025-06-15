# infra/storage.tf

# A random string to ensure the storage account name is globally unique
resource "random_string" "storage_suffix" {
  length  = 6
  special = false
  upper   = false
}

# --- Azure Storage Account ---
resource "azurerm_storage_account" "pfa_storage" {
  name                     = "pfastorage${random_string.storage_suffix.result}"
  resource_group_name      = module.resource_group.name
  location                 = module.resource_group.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # Locally-redundant storage is the cheapest and sufficient
}

# --- Azure Storage Container ---
# This creates a container named 'avatars' inside the storage account
resource "azurerm_storage_container" "avatars_container" {
  name                  = "avatars"
  storage_account_name  = azurerm_storage_account.pfa_storage.name
  container_access_type = "blob" # 'blob' access allows public read for the images
}