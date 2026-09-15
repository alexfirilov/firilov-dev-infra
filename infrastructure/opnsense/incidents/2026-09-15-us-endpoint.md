# US Proton endpoint unavailable — 2026-09-15

## Diagnosis

Seerr reported the default US route unavailable, affecting Netflix (US override)
and Prime Video (following the US default). Max and Disney+ used direct Israel
and remained healthy. The GB and AR tunnels also had fresh handshakes and healthy
gateways.

The existing watchdog first reported a stale US handshake at 06:08 UTC, 385
seconds after the last handshake (approximately 06:01:35 UTC). Its subsequent
US-only restarts did not restore connectivity.

A packet capture on OPNsense at 10:36 UTC showed the endpoint `72.14.148.25`
returning ICMP **UDP port 51820 unreachable** in response to WireGuard handshake
requests. The same endpoint answered ICMP echo requests. Selecting a fresh
local UDP port also received the explicit port-unreachable responses and did
not establish a handshake. The temporary local-port test was reverted.

The rename from `WG_PROTON` to `WG_PROTON_US` changed only the interface
label. Its stable assignment is still `opt1`, device `wg0`, and gateway
`WG_PROTON_GW`. The interface remained in the `wireguard` group. The running
client key and peer key matched the saved configuration. No rename rollback
or changes to the healthy tunnels were needed.

## Recovery

The unavailable remote WireGuard service cannot be restored by clearing TV
connections or repeatedly restarting the local tunnel. Replace the US profile
with a working US configuration from Proton, preserving the existing instance,
peer and policy identifiers, tunnel address and DNS route. Follow
[Proton's configuration download instructions](https://protonvpn.com/support/wireguard-configurations).

At diagnosis time no replacement US configuration was available locally. The
owner authorized the Claude Code agent on the Ubuntu desktop to obtain one
through its Proton browser session. That session had expired, so the browser
was opened for the owner to sign in again. Existing country selections remain
in place while the replacement is obtained.

Seerr revision `8f885c5` names unavailable countries and explains that
Reconnect TV refreshes TV connections, while an unavailable VPN connection
requires repair or selection of another country. All 173 tests, type checks,
formatting, translation extraction checks and lint passed (no lint errors;
19 existing warnings). The Flux deployment is healthy. Desktop and 390px
mobile browser checks passed without JavaScript errors; simulated outage and
recovery statuses correctly show and remove the warning, and route controls
remain usable. The mobile menu fits within the viewport.

After installing a replacement, verify the US handshake, gateway health,
DNS and independent egress-country probes, then verify authenticated broker
status and the deployed Seerr controls. Clear stale TV connections after a
confirmed repair. Record the result below.

Pre-repair router backup: `/root/vpn-us-repair-20260915T105106Z/`.

Recovery validation (2026-09-15, completed):

- Replacement server: Proton **US-NY#602** (New York, Plus tier), endpoint
  `193.148.18.82:51820`. Obtained via the authenticated Proton browser session
  on the Ubuntu desktop after the owner re-signed in.
- Installed into the existing US profile (instance
  `7245b85a-60a3-45a2-84e0-c5a96f9b616d`, peer, tunnel address `10.2.0.2/32`,
  DNS `10.2.0.1`, gateway `WG_PROTON_GW`) via `replace-us-profile.php`; only the
  server private key, client public key, peer public key and endpoint changed.
  No other tunnels, keys, policies or the interface rename were touched.
- Post-restart runtime: `wg0` peer matches config, endpoint
  `193.148.18.82:51820`, fresh handshake (<60 s), bidirectional transfer.
- Gateway `WG_PROTON_GW` Online, 0.0% loss, ~150 ms (consistent US-from-IL RTT).
- Egress-country probe through the US gateway resolved to **United States**
  (exit `193.148.18.87`, Proton/M247), confirming geo, not just tunnel liveness.
- Authenticated Seerr broker `/v1/status` reports `connected: true`, `country:
  US`; all service routes connected (Max→IL, Netflix→US, Prime Video→US,
  Disney+→IL).

Any TV app left mid-session on a US-routed service during the outage may still
hold a dead connection through the old endpoint; use Seerr's "Reconnect TV" to
flush it, or wait for the app to re-establish.
