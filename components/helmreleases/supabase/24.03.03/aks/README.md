# Supabase on Azure Kubernetes Service (AKS)

This directory contains AKS-specific configurations for Supabase deployment.

## Key Differences from Base Configuration

1. **Storage**: Uses Azure CSI disk provisioner (`disk.csi.azure.com`) with Premium_LRS storage
2. **Load Balancer**: Configured as internal Azure Load Balancer instead of AWS ALB
3. **Resource Limits**: Optimized for AKS node sizes and Azure VM performance characteristics
4. **Persistence**: All stateful components (DB, Storage, Imgproxy) use Azure managed disks

## Components

- `storageclass.yaml`: Defines Azure CSI disk storage class with Premium SSD
- `helmrelease-patch.yaml`: AKS-specific overrides for the base Helm release
- `kustomization.yaml`: Combines base configuration with AKS-specific resources
- `namespace.yaml`: Creates the supabase namespace
- `externalsecrets.yaml`: External secrets configuration
- `secretstore.yaml`: Secret store configuration

## Deployment

```bash
kubectl apply -k .
```

## Storage Configuration

All persistent volumes use the `managed-csi-premium` storage class:
- Database: 32Gi
- Storage: 20Gi  
- Imgproxy: 10Gi

## Network Configuration

Kong is exposed via an internal Azure Load Balancer. To access from outside the cluster, you'll need to configure additional networking (e.g., Application Gateway, Azure Front Door).