# vpn-orchestrator

Broker that sits between Seerr (stream-first fork) and the OPNsense TV VPN
control plane. Seerr holds no OPNsense credentials; it can only ask this
service to move the TV route to an allowlisted country.

Source: https://github.com/alexfirilov/vpn-orchestrator
Router plugin: https://github.com/alexfirilov/opnsense-vpn-orchestrator-plugin

## Not wired into `apps/production` yet

This directory is deliberately absent from `apps/production/kustomization.yaml`.
The broker cannot become ready until the router side exists, and Flux would
otherwise deploy a service that can never pass its readiness probe.

## Prerequisites, in order

1. **Install the OPNsense plugin** on the router and provision one WireGuard
   country profile per entry in `ALLOWED_COUNTRIES`. Proton profiles for GB and
   IL are not yet imported, so today only US would actually switch.
2. **Create the broker identity** in OPNsense with the
   `VPN Orchestrator: TV route control` privilege only, and note its API key
   and secret. Do not reuse an administrator key.
3. **Create the secrets** (SOPS-encrypted, matching this repo's convention):

   - `vpn-orchestrator-secrets` in namespace `vpn-orchestrator`, keys
     `broker-token`, `opnsense-api-key`, `opnsense-api-secret`.
   - `vpn-orchestrator-opnsense-ca` ConfigMap, key `ca.crt`, holding the
     router's CA certificate. TLS verification is not optional.
   - `seerr-stream-first` in namespace `jellyseerr`, keys
     `SEERR_STREAM_FIRST_BROKER_URL` and `SEERR_STREAM_FIRST_BROKER_API_KEY`.
     `broker-token` and the Seerr key must be the same value, at least 32
     characters. Set both keys or neither: Seerr refuses to combine one
     externally managed credential with a settings value and fails closed.
   - `ghcr-pull` (`kubernetes.io/dockerconfigjson`) in both namespaces. Both
     images live in private GHCR packages, so a PAT with `read:packages` is
     required or the pods will sit in ImagePullBackOff.

4. **Add `- ../base/vpn-orchestrator`** to `apps/production/kustomization.yaml`
   and merge to `main`.
5. **Enable stream-first** in the Seerr admin UI. It ships disabled, so the
   fork image behaves exactly like upstream until this is turned on.

## Rollback

Revert the `image` block in `apps/base/jellyseerr/helmrelease.yaml` to drop
back to the upstream chart default, and remove this directory from
`apps/production`. The Seerr config PVC is retained on uninstall, and the fork
only ever adds a nullable `user_settings.streamingProviderFamilies` column, so
downgrading to upstream v3.4.1 does not lose data.
