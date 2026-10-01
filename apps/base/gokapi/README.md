# Gokapi

Browser file transfer at https://files.firilov.dev/admin. Flux includes this app
through `apps/production/kustomization.yaml`.

Every URL, including download links and the API, requires HTTP Basic authentication
at the Caddy sidecar. The usernames are `admin` and `alexf`; both currently use the same password.
The bootstrap password and bcrypt hash are in
the SOPS-encrypted `gokapi-bootstrap` Secret. Gokapi uses header authentication,
accepts only registered users, and listens on loopback inside the pod. Caddy
overwrites the identity header with the authenticated username. Only Caddy's port
is exposed by the Service.

Gokapi v2.2.4 stores configuration, SQLite and files on the `gokapi` local-path
PVC. The pod prefers k3s2; the resulting volume stays on the node where it was
provisioned. Recreate deployment strategy prevents overlapping SQLite writers.
The requested 20Gi is provisioning metadata; local-path does not enforce a disk
quota. The file limit is 5120 MB and uploads use 10 MB chunks to keep requests short on slower connections.

The custom admin script seeds browser preferences to one-day expiration and
unlimited downloads. Users can change these before uploading; they are defaults,
not a server-enforced retention ceiling. Gokapi automatically deletes expired
files during its hourly cleanup (and on startup); expired links stop working
immediately. Storage snapshots/backups, if added separately, have their own retention.

Cloudflare terminates public HTTPS. The remotely managed `k3s1` tunnel has a
`files.firilov.dev` ingress to the existing Envoy Gateway at `http://10.100.102.54`.
A proxied DNS CNAME points to `1c72bb9f-421f-4927-a136-7a373428313f.cfargotunnel.com`.
Its other ingress entries and the existing cloudflared Deployment are preserved.
HTTPRoute request timeouts are disabled for large downloads.

Bootstrap copies the seed configuration and creates the admin only on a fresh
volume. Later restarts preserve existing configuration and users. To rotate the
site password, update `basic-auth-hash` in the encrypted Secret, then restart the
Deployment after Flux reconciles. Header authentication means Gokapi's seeded
password does not control site access. Bootstrap credentials can be rotated
independently for a future clean deployment.
