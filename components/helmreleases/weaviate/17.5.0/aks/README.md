# Weaviate on AKS

This directory contains Azure Kubernetes Service (AKS) specific overlays for deploying Weaviate.

## Key Azure-Specific Configurations

1. **Storage Class**: Uses `disk.csi.azure.com` provisioner (NOT `file.csi.azure.com`)
   - Premium SSD storage for better performance
   - Configured with `managed-csi-premium` storage class

2. **Load Balancer**: Configured as internal load balancer for security

3. **Resources**: Optimized for Azure VM sizes with appropriate memory and CPU limits

## Important Notes

⚠️ **Critical**: Do NOT use `file.csi.azure.com` provisioner as it causes file corruptions in Weaviate.

## Deployment

To deploy using Flux CD, reference this AKS directory in your cluster configuration:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: weaviate
  namespace: flux-system
spec:
  interval: 10m
  path: ./components/helmreleases/weaviate/17.5.0/aks
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
```