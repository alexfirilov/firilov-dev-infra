# vpn-orchestrator

Broker that sits between Seerr (stream-first fork) and the OPNsense TV VPN
control plane. Seerr holds no OPNsense credentials; it can only ask this
service to move the TV route to an allowlisted country.

Source: https://github.com/alexfirilov/vpn-orchestrator
Router plugin: https://github.com/alexfirilov/opnsense-vpn-orchestrator-plugin

## Deployed

Wired into `apps/production` on 2026-08-23, once the router side was configured
and `configctl vpn_orchestrator validate` returned clean.

`ALLOWED_COUNTRIES` is `US,IL` for the current proof of concept: US routes
through the Proton tunnel, IL is the direct ISP path with WireGuard off.

## Cluster state that is deliberately not in git

These hold credentials or machine-specific material and were created with
kubectl, not committed:

- `vpn-orchestrator-secrets` — `broker-token`, `opnsense-api-key`,
  `opnsense-api-secret`. The OPNsense pair belongs to the `vpn-orchestrator-broker`
  user, which holds only the `page-vpn-orchestrator-control` privilege.
- `vpn-orchestrator-opnsense-ca` — the router's self-signed web certificate,
  used as the trust root for `https://opnsense.internal`. It expires
  **2027-08-07**, and OPNsense regenerating its web certificate would also
  invalidate it; either event breaks the broker until this is refreshed.
- `ghcr-pull` in both namespaces — the images are private GHCR packages.
- `seerr-stream-first` in `jellyseerr` — the broker URL and API key. Seerr reads
  the two together and fails closed if only one is present.

Source of truth for the credential values is
`/root/vpn-orchestrator-api-credentials.txt` on the PVE host (mode 0600).
Move these into SOPS to make a cluster rebuild reproducible.

## Rollback

Revert the `image` block in `apps/base/jellyseerr/helmrelease.yaml` to drop
back to the upstream chart default, and remove this directory from
`apps/production`. The Seerr config PVC is retained on uninstall, and the fork
only ever adds a nullable `user_settings.streamingProviderFamilies` column, so
downgrading to upstream v3.4.1 does not lose data.
