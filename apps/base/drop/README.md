# drop

A small clipboard and file drop at https://drop.firilov.dev, replacing the
Opengist and Gokapi use cases. Source code and image builds live in the private
repo `alexfirilov/drop`; images are `ghcr.io/alexfirilov/drop:sha-<short>`.
Flux includes this app through `apps/production/kustomization.yaml`.

drop handles authentication itself, with admin-created users and session
cookies. Recipients of public links (`/s/...`) need no account; a link can
have a PIN, a use limit (including one-time) and an expiry. Cloudflare and
Envoy provide HTTPS and routing. drop trusts `CF-Connecting-IP` /
`X-Forwarded-For` only from the pod network (`10.42.0.0/16`), and uses it for
login rate limiting.

State lives on the `drop` local-path PVC: `drop.db` (SQLite), `files/`, and
`tmp/` for partial uploads, which are kept on the PVC so 30 GiB uploads don't
fill an emptyDir. The pod prefers k3s2 and uses a Recreate strategy because
SQLite needs a single writer. Uploads are sent in 8 MiB chunks, which keeps
each request well under Cloudflare's 100 MB limit, and HTTPRoute timeouts are
disabled for large downloads.

## Secrets

`drop-secrets` (SOPS) holds:
- `secret`, the password pepper and CSRF key. **Never change it once users
  exist**, because every password stops working.
- `admin-password`, the initial password for `alexf`, used only when the
  database has no users. Later password changes happen in the app.

The image is a private GHCR package. Like `vpn-orchestrator`, the namespace
needs a `ghcr-pull` docker-registry Secret, created by hand:

    kubectl get secret ghcr-pull -n vpn-orchestrator -o yaml \
      | sed 's/namespace: vpn-orchestrator/namespace: drop/' \
      | grep -vE '^\s+(uid|resourceVersion|creationTimestamp):' \
      | kubectl apply -f -

## Cloudflare

The remotely managed `k3s1` tunnel needs a public hostname `drop.firilov.dev`
pointing to `http://10.100.102.54` (Envoy Gateway). Adding the hostname in
Zero Trust also creates the proxied DNS CNAME.

## Upgrades

Bump the `sha-` tag in `deployment.yaml` to the image CI built for the wanted
commit of `alexfirilov/drop`.
