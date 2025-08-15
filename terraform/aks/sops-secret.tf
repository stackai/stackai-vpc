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

  # Cleanup kubeconfig
  provisioner "local-exec" {
    when    = destroy
    command = "rm -f ${self.triggers.kubeconfig_file}"
  }
}