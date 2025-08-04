# Create a ConfigMap with Terraform outputs for use by Flux
resource "kubernetes_config_map" "terraform_outputs" {
  metadata {
    name      = "terraform-outputs"
    namespace = "flux-system"
  }

  data = {
    # Azure tenant and subscription information
    AZURE_TENANT_ID       = data.azurerm_client_config.current.tenant_id
    AZURE_SUBSCRIPTION_ID = data.azurerm_client_config.current.subscription_id
    
    # Cluster information
    CLUSTER_NAME          = var.cluster_name
    RESOURCE_GROUP        = azurerm_resource_group.aks.name
    LOCATION              = azurerm_resource_group.aks.location
    
    # Network information
    VNET_ID               = azurerm_virtual_network.aks.id
    VNET_NAME             = azurerm_virtual_network.aks.name
    SUBNET_ID             = azurerm_subnet.aks.id
    
    # OIDC information for workload identity
    OIDC_ISSUER_URL       = azurerm_kubernetes_cluster.aks.oidc_issuer_url
    
    # Managed Identity Client IDs (for workload identity)
    AZURE_DISK_CSI_CLIENT_ID  = azurerm_user_assigned_identity.azure_disk_csi.client_id
    AZURE_FILE_CSI_CLIENT_ID  = azurerm_user_assigned_identity.azure_file_csi.client_id
    
    # Key Vault information
    KEY_VAULT_NAME        = azurerm_key_vault.main.name
    KEY_VAULT_URI         = azurerm_key_vault.main.vault_uri
  }

  depends_on = [
    azurerm_kubernetes_cluster.aks,
    null_resource.create_flux_ns
  ]
}
