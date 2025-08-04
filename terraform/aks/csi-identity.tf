# Managed Identity for Azure Disk CSI Driver
resource "azurerm_user_assigned_identity" "azure_disk_csi" {
  name                = "${var.cluster_name}-azure-disk-csi-identity"
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  tags                = var.tags
}

# Federated credential for Azure Disk CSI Driver
resource "azurerm_federated_identity_credential" "azure_disk_csi" {
  name                = "azure-disk-csi-federated"
  resource_group_name = azurerm_resource_group.aks.name
  audience            = ["api://AzureADTokenExchange"]
  parent_id           = azurerm_user_assigned_identity.azure_disk_csi.id
  issuer              = azurerm_kubernetes_cluster.aks.oidc_issuer_url
  subject             = "system:serviceaccount:kube-system:csi-azuredisk-node-sa"
}

# Role assignment for Azure Disk CSI to manage disks
resource "azurerm_role_assignment" "azure_disk_csi_contributor" {
  scope                = azurerm_resource_group.aks.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.azure_disk_csi.principal_id
}

# Managed Identity for Azure File CSI Driver
resource "azurerm_user_assigned_identity" "azure_file_csi" {
  name                = "${var.cluster_name}-azure-file-csi-identity"
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  tags                = var.tags
}

# Federated credential for Azure File CSI Driver
resource "azurerm_federated_identity_credential" "azure_file_csi" {
  name                = "azure-file-csi-federated"
  resource_group_name = azurerm_resource_group.aks.name
  audience            = ["api://AzureADTokenExchange"]
  parent_id           = azurerm_user_assigned_identity.azure_file_csi.id
  issuer              = azurerm_kubernetes_cluster.aks.oidc_issuer_url
  subject             = "system:serviceaccount:kube-system:csi-azurefile-node-sa"
}

# Role assignment for Azure File CSI to manage storage accounts
resource "azurerm_role_assignment" "azure_file_csi_contributor" {
  scope                = azurerm_resource_group.aks.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.azure_file_csi.principal_id
}