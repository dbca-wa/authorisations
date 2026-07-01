# Kustomize Configuration

This directory contains Kubernetes manifests for Authorisations using Kustomize.

**For complete deployment documentation, see [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).**

## Quick reference

Do not apply `base/` directly—always use an overlay:

```bash
# UAT
kubectl apply -k overlays/uat/ --namespace=authorisations

# Production
kubectl apply -k overlays/prod/ --namespace=authorisations
```

See [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for:
- Full configuration details
- Environment setup
- Preflight validation
- Production deployment procedures

#### UAT

```bash
# Dry run
kubectl apply -k kustomize/overlays/uat/ --namespace=authorisations --dry-run=server

# Apply
kubectl apply -k kustomize/overlays/uat/ --namespace=authorisations
```

#### Production

**Ensure you are connected to the correct production cluster context before running these commands.**

```bash
# Verify you are connected to production
kubectl config current-context

# Dry run
kubectl apply -k kustomize/overlays/prod/ --namespace=authorisations --dry-run=server

# Apply
kubectl apply -k kustomize/overlays/prod/ --namespace=authorisations
```

## References

- [Kubernetes Kustomize Documentation](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [Kustomize GitHub Repository](https://github.com/kubernetes-sigs/kustomize)
- [Kustomize Examples](https://github.com/kubernetes-sigs/kustomize/tree/master/examples)
