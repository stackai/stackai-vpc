# Virtual Network
resource "azurerm_virtual_network" "aks" {
  name                = "${var.cluster_name}-vnet"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  address_space       = [var.vnet_cidr]
  
  tags = var.tags
}

# AKS Subnet
resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.aks.name
  virtual_network_name = azurerm_virtual_network.aks.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 4, 0)]
}

# Additional subnets for other services (similar to EKS public/private)
resource "azurerm_subnet" "public" {
  name                 = "public-subnet"
  resource_group_name  = azurerm_resource_group.aks.name
  virtual_network_name = azurerm_virtual_network.aks.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 4, 1)]
}

resource "azurerm_subnet" "private" {
  name                 = "private-subnet"
  resource_group_name  = azurerm_resource_group.aks.name
  virtual_network_name = azurerm_virtual_network.aks.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 4, 2)]
}

# Network Security Group for AKS subnet
resource "azurerm_network_security_group" "aks" {
  name                = "${var.cluster_name}-nsg"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  
  tags = var.tags
}

# Security rule to allow port 8000
# TODO REMOVE THIS ONCE SUPABASE IS firxed
resource "azurerm_network_security_rule" "allow_8000" {
  name                        = "allow-port-8000"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "8000"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.aks.name
  network_security_group_name = azurerm_network_security_group.aks.name
}

# Security rule to allow port 80 (HTTP)
resource "azurerm_network_security_rule" "allow_80" {
  name                        = "allow-port-80"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.aks.name
  network_security_group_name = azurerm_network_security_group.aks.name
}

# Security rule to allow port 443 (HTTPS)
resource "azurerm_network_security_rule" "allow_443" {
  name                        = "allow-port-443"
  priority                    = 120
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "443"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.aks.name
  network_security_group_name = azurerm_network_security_group.aks.name
}

# Associate NSG with AKS subnet
resource "azurerm_subnet_network_security_group_association" "aks" {
  subnet_id                 = azurerm_subnet.aks.id
  network_security_group_id = azurerm_network_security_group.aks.id
}
