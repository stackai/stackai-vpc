terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  # You'll want to change this to your preferred backend
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# Validate environment before proceeding
data "external" "validate_environment" {
  program = ["bash", "${path.module}/scripts/validate-environment.sh"]
}

# Get current Azure client configuration
data "azurerm_client_config" "current" {}

# Get current user from system
data "external" "whoami" {
  program = ["sh", "-c", "echo '{\"user\": \"'$(whoami)'\"}'"]
}

locals {
  # Use provided user_suffix or fall back to system username
  effective_user_suffix = var.user_suffix != "" ? var.user_suffix : data.external.whoami.result.user
}

# Configure the Kubernetes provider
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
}

# Resource group
resource "azurerm_resource_group" "aks" {
  name     = "${var.cluster_name}-${local.effective_user_suffix}-rg"
  location = var.location
  tags     = merge(var.tags, { Owner = local.effective_user_suffix })
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.cluster_name}-${local.effective_user_suffix}"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = "${var.cluster_name}-${local.effective_user_suffix}"
  kubernetes_version  = var.kubernetes_version

  # Enable workload identity and OIDC for pod authentication
  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  default_node_pool {
    name       = "default"
    node_count = var.node_count
    vm_size    = var.node_size
    
    # Use Azure CNI for better integration
    vnet_subnet_id = azurerm_subnet.aks.id
    
    enable_auto_scaling = true
    min_count          = var.min_node_count
    max_count          = var.max_node_count
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = var.service_cidr
    dns_service_ip    = var.dns_service_ip
  }

  tags = merge(var.tags, { Owner = local.effective_user_suffix })
}

# Memory-optimized node pool with 8 vCPUs and 64GB RAM
resource "azurerm_kubernetes_cluster_node_pool" "memory_optimized" {
  name                  = "memopt"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size              = var.memory_node_size
  node_count           = var.memory_node_count
  
  # Use the same subnet as the default pool
  vnet_subnet_id = azurerm_subnet.aks.id
  
  enable_auto_scaling = true
  min_count          = var.memory_min_node_count
  max_count          = var.memory_max_node_count
  
  # Node labels to help with pod scheduling
  node_labels = {
    "nodepool" = "memory-optimized"
    "workload" = "memory-intensive"
  }
  
  # Node taints if you want to ensure only specific pods run on these nodes
  node_taints = ["workload=memory-intensive:NoSchedule"]
  
  tags = merge(var.tags, { 
    Owner = local.effective_user_suffix,
    NodePool = "memory-optimized"
  })
}
