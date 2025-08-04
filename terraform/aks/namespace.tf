resource "null_resource" "create_flux_ns" {
  provisioner "local-exec" {
    command = <<-EOT
      export KUBECONFIG="$(mktemp)"
      echo '${azurerm_kubernetes_cluster.aks.kube_config_raw}' > "$KUBECONFIG"
      kubectl get ns flux-system || kubectl create ns flux-system
    EOT
    interpreter = ["/bin/bash", "-c"]
  }

  triggers = {
    cluster_endpoint = azurerm_kubernetes_cluster.aks.kube_config.0.host
  }

  depends_on = [azurerm_kubernetes_cluster.aks]
}