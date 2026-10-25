# Gokapi

Browser file transfer at https://files.firilov.dev/admin. Flux includes this app
through `apps/production/kustomization.yaml`.

Gokapi handles authentication with its native username/password login and session
cookies at `/login`. The Service sends traffic directly to Gokapi; there is no
authentication sidecar or trusted identity header. Cloudflare and Envoy provide
HTTPS and routing. Gokapi trusts forwarded client IP information from Envoy in
the cluster pod network (`10.42.0.0/16`).

The migration gives existing `admin` and `alexf` accounts their previous site
password, held in the SOPS-encrypted `gokapi-bootstrap` Secret. Account IDs,
permissions, file ownership and encryption salts are preserved. The `native-auth`
init container backs up the original configuration and SQLite database in
`/app/state/config/native-auth-backup` before migrating header authentication.
Migration runs once; later starts preserve passwords changed through Gokapi.
Other existing accounts are preserved. Fresh volumes create the initial `admin`
account; additional users can be created through Gokapi's Users page.

Account login protects uploads, administration and user management. Recipients
can use download links without an account; use Gokapi's share password setting
when a download should require a password. Expiration and download limits still
apply. API access uses Gokapi API keys.

Gokapi v2.2.4 stores configuration, SQLite and files on the `gokapi` local-path
PVC. The pod prefers k3s2; the resulting volume stays on the node where it was
provisioned. Recreate deployment strategy prevents overlapping SQLite writers.
The requested 20Gi is provisioning metadata; local-path does not enforce a disk
quota. The file limit is 30720 MB (30 GiB) and uploads use 2 MB chunks, one at a time, to keep requests short and avoid splitting slower connections across concurrent uploads. The bootstrap init container reconciles the persisted file limit and chunk settings on every startup, including for existing volumes.

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
volume. Later restarts preserve existing configuration and users while enforcing
native authentication and the externally accessible listener. Change account
passwords through Gokapi. Updating `bootstrap-password` in the encrypted Secret
affects future clean deployments, not existing native accounts.

Custom scripts use a generated ConfigMap; Kustomize's content hash triggers a
rollout when they change. The Python init image is pinned by digest. Run migration
checks with `python3 -B -m unittest discover -s tests -v`, and render the app with
`kubectl kustomize apps/base/gokapi` before committing changes.
