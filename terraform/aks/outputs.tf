output "cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "cluster_id" {
  description = "ID of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.id
}

output "kube_config" {
  description = "Kubernetes config for connecting to the cluster"
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "kube_config_host" {
  description = "Kubernetes API server endpoint"
  value       = azurerm_kubernetes_cluster.aks.kube_config.0.host
  sensitive   = true
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.aks.name
}

output "vnet_id" {
  description = "ID of the Virtual Network"
  value       = azurerm_virtual_network.aks.id
}

output "vnet_name" {
  description = "Name of the Virtual Network"
  value       = azurerm_virtual_network.aks.name
}

output "aks_subnet_id" {
  description = "ID of the AKS subnet"
  value       = azurerm_subnet.aks.id
}

output "cluster_identity_principal_id" {
  description = "Principal ID of the cluster managed identity"
  value       = azurerm_kubernetes_cluster.aks.identity.0.principal_id
}

output "node_resource_group" {
  description = "Name of the auto-generated resource group for AKS nodes"
  value       = azurerm_kubernetes_cluster.aks.node_resource_group
}

# Workload Identity outputs
output "oidc_issuer_url" {
  description = "OIDC issuer URL for workload identity"
  value       = azurerm_kubernetes_cluster.aks.oidc_issuer_url
}

output "azure_disk_csi_identity_client_id" {
  description = "Client ID of the Azure Disk CSI managed identity"
  value       = azurerm_user_assigned_identity.azure_disk_csi.client_id
}

output "azure_file_csi_identity_client_id" {
  description = "Client ID of the Azure File CSI managed identity"
  value       = azurerm_user_assigned_identity.azure_file_csi.client_id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "post_deployment_complete" {
  description = "Confirmation that all post-deployment steps completed"
  value       = "Post-deployment completed at ${null_resource.create_login_user.id}"
  depends_on  = [null_resource.create_login_user]
}