variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "fullStack-cluster"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "vnet_cidr" {
  description = "CIDR block for Virtual Network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "service_cidr" {
  description = "CIDR block for Kubernetes services"
  type        = string
  default     = "10.1.0.0/16"
}

variable "dns_service_ip" {
  description = "DNS service IP address (must be within service_cidr)"
  type        = string
  default     = "10.1.0.10"
}

variable "kubernetes_version" {
  description = "Kubernetes version for AKS"
  type        = string
  default     = "1.31"
}

variable "node_count" {
  description = "Initial number of nodes"
  type        = number
  default     = 2
}

variable "min_node_count" {
  description = "Minimum number of nodes for autoscaling"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes for autoscaling"
  type        = number
  default     = 3
}

variable "node_size" {
  description = "Size of the nodes"
  type        = string
  default     = "Standard_D2_v3"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "fullStack-cluster"
    ManagedBy   = "terraform"
  }
}