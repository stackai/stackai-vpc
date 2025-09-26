#!/bin/bash

# Universal Docker installation script for Ubuntu/Debian and Red Hat/CentOS/Fedora systems
# This script detects the OS and installs Docker accordingly

set -e  # Exit on any error

echo "Starting Docker installation..."

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        echo "Detected OS: $PRETTY_NAME"
    else
        echo "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi
}

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    echo "Installing Docker for Ubuntu/Debian..."
    
    # Update package index
    sudo apt-get update
    
    # Install prerequisites
    sudo apt-get install -y ca-certificates curl
    
    # Create keyrings directory
    sudo install -m 0755 -d /etc/apt/keyrings
    
    # Add Docker's official GPG key
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    
    # Add the repository to Apt sources
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package index again
    sudo apt-get update
    
    # Install Docker packages
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

# Function to install Docker on Red Hat/CentOS/Fedora
install_docker_redhat() {
    echo "Installing Docker for Red Hat/CentOS/Fedora..."
    
    # Add Docker repository
    sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
    
    # Install Docker packages
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

# Function to configure Docker service and user permissions
configure_docker() {
    echo "Configuring Docker service and user permissions..."
    
    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    sudo groupadd docker 2>/dev/null || true  # Ignore error if group already exists
    sudo usermod -aG docker $USER
    
    echo "Docker installation completed."
    
    # Test if docker group is already active in current session
    if docker ps >/dev/null 2>&1; then
        echo "Docker group active."
    else
        echo "Activating docker group - replacing shell..."
        exec su - $USER -c "
            echo 'Docker group activated.'
            docker --version
            docker compose version
            cd '$PWD'
            exec \$SHELL
        "
    fi
    
    echo "Verify: docker --version && docker ps"
    echo ""
    echo "Follow the README.md file to continue with the setup."
}

# Main installation logic
main() {
    detect_os
    
    case $OS in
        ubuntu|debian)
            install_docker_ubuntu
            ;;
        rhel|centos|fedora|rocky|almalinux)
            install_docker_redhat
            ;;
        *)
            echo "Unsupported OS: $OS"
            echo "This script supports Ubuntu, Debian, Red Hat Enterprise Linux, CentOS, Fedora, Rocky Linux, and AlmaLinux."
            exit 1
            ;;
    esac
    
    configure_docker
}

# Run main function
main