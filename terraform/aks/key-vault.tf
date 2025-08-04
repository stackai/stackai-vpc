# Create a Key Vault for storing secrets
resource "azurerm_key_vault" "main" {
  name                = "${substr(replace(var.cluster_name, "-", ""), 0, 20)}kv"
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Enable RBAC authorization
  enable_rbac_authorization = true

  # Soft delete and purge protection
  soft_delete_retention_days = 7
  purge_protection_enabled   = false # Set to true in production

  tags = var.tags
}

# Grant the current user/service principal access to manage secrets
resource "azurerm_role_assignment" "current_user_key_vault_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}