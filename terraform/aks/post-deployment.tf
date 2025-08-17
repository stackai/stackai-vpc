# Post-deployment configuration for AKS cluster
# This file handles all the steps that need to happen after the cluster is created:
# 1. Apply SOPS secret for Flux decryption
# 2. Bootstrap Flux to the cluster
# 3. Wait for Flux to reconcile all resources
# 4. Create initial login user for testing

# Apply SOPS secret as the very last step
resource "null_resource" "apply_sops_secret" {
  # Ensure flux-system namespace exists before applying the secret
  depends_on = [
    null_resource.create_flux_ns
  ]

  # Re-run if cluster changes
  triggers = {
    cluster_id = azurerm_kubernetes_cluster.aks.id
    kubeconfig_file = "${path.module}/kubeconfig_${var.cluster_name}_${local.effective_user_suffix}"
    always_run = timestamp()
  }

  # Save kubeconfig for the script
  provisioner "local-exec" {
    when    = create
    command = <<-EOT
      echo '${azurerm_kubernetes_cluster.aks.kube_config_raw}' > ${self.triggers.kubeconfig_file}
      chmod 600 ${self.triggers.kubeconfig_file}
    EOT
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/scripts/apply-sops-secret.sh"
    
    environment = {
      KUBECONFIG = self.triggers.kubeconfig_file
    }
  }
}

# Bootstrap Flux after SOPS secret is applied
resource "null_resource" "bootstrap_flux" {
  depends_on = [
    null_resource.apply_sops_secret
  ]

  triggers = {
    cluster_id = azurerm_kubernetes_cluster.aks.id
    kubeconfig_file = "${path.module}/kubeconfig_${var.cluster_name}_${local.effective_user_suffix}"
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/scripts/flux-bootstrap-aks.sh"
    
    environment = {
      KUBECONFIG = self.triggers.kubeconfig_file
      # GITHUB_TOKEN is inherited from the parent environment
    }
  }
}

# Sleep for 10 minutes to allow Flux to reconcile
resource "null_resource" "wait_for_flux" {
  depends_on = [
    null_resource.bootstrap_flux
  ]

  triggers = {
    cluster_id = azurerm_kubernetes_cluster.aks.id
    kubeconfig_file = "${path.module}/kubeconfig_${var.cluster_name}_${local.effective_user_suffix}"
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "⏳ Waiting 10 minutes for Flux to reconcile all resources..."
      sleep 600
      echo "✅ Wait complete"
    EOT
  }
}

# Create login user after Flux has reconciled
resource "null_resource" "create_login_user" {
  depends_on = [
    null_resource.wait_for_flux
  ]

  triggers = {
    cluster_id = azurerm_kubernetes_cluster.aks.id
    kubeconfig_file = "${path.module}/kubeconfig_${var.cluster_name}_${local.effective_user_suffix}"
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/scripts/create_login_user.sh"
    
    working_dir = path.root
    
    environment = {
      KUBECONFIG = "${path.module}/${self.triggers.kubeconfig_file}"
    }
  }

  # Cleanup kubeconfig after all operations complete
  provisioner "local-exec" {
    when    = destroy
    command = "rm -f ${self.triggers.kubeconfig_file}"
  }
}