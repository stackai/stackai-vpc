# Contributing to StackAI BYOC

## Development Aliases

### `k` - Kubectl Shorthand

```bash
alias 'k'='kubectl'
```

### `rws` - Reconcile Workspace

The `rws` alias is a convenient command for reconciling all Flux Kustomizations.

```bash
alias 'rws'='flux reconcile ks -n flux-system flux-system --with-source; flux reconcile ks -n flux-system crds; flux reconcile ks -n flux-system system; flux reconcile ks -n flux-system stackend; flux reconcile ks -n flux-system stackweb; k get pods -n flux-system'
```

## Git Repository Management

### Changing the Target Branch

```bash
kubectl edit gitrepo -n flux-system
```

Edit the `spec.ref.branch` field to change which branch Flux tracks:

```yaml
spec:
  ref:
    branch: main # Change to your desired branch
```
