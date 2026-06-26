# SUPERSEDED — the etzhayyim PDS no longer runs on Kubernetes

The TypeScript/Bun PDS that used to live here (Deployment + Service + StatefulSet-style
PV + k8s Secret) has been **removed**. The independent etzhayyim atproto PDS now runs
**k8s-free on the Murakumo mesh**:

- **State** = the kotoba Datom log on the local kotoba engine (`KotobaStore`), not a PV.
- **Run** = a launchd LaunchAgent (`bb serve`), not a Deployment/kubelet.
- **Ingress** = a Cloudflare Tunnel, not a Service/LoadBalancer.
- **Signing** = an actor-sealed P-256 keystore (present-only, no-server-key), not a k8s Secret.

→ See **`50-infra/etzhayyim-atproto-pds-clj/deploy/README.md`** for the current deployment.

(This breadcrumb is kept so links/references to this path land somewhere useful; the
directory otherwise holds no deployable artifacts.)
