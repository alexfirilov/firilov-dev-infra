# OPNsense TV service routing

Deployed 2026-09-10/11 on OPNsense 26.7.2_2 (`10.100.102.254`).
The sole target is the Ethernet LG TV at `10.100.102.190`.

## Ownership

Flux deploys the broker and Seerr images from `apps/base`. The router plugin is
installed manually from [opnsense-vpn-orchestrator-plugin](https://github.com/alexfirilov/opnsense-vpn-orchestrator-plugin),
currently runtime revision `b78b6e9`. Its installed file manifest includes the
new `vpn_orchestrator/service_routing.py` module. Flux does not reconcile the
OPNsense configuration.

`service-routing.json` is a non-secret copy of the administrator-owned mapping
at `/usr/local/etc/vpn-orchestrator/service-routing.json` on the appliance.
It records fixed firewall rule UUIDs, domain suffixes and external alias names.
The enabled firewall rules in `/conf/config.xml` remain the source of truth for
live selections; changing a dropdown does not require a Git commit.

## Routes and DNS

| Route | Interface | Tunnel source | DNS | Purpose |
| --- | --- | --- | --- | --- |
| Israel | vtnet0 / ISP | direct NAT | 1.1.1.1 | HBO Max override |
| United States | wg0 | 10.2.0.2/32 | 10.2.0.1 | Netflix override |
| United Kingdom | wg1 | 10.3.0.2/32 | 10.3.0.1 | Prime Video override |

Disney+ follows the independently selected default (US at validation time).
Both tunnels remain running, using separate Proton-supported tunnel addresses.

TV TCP/UDP port 53 is redirected to dnsmasq at 127.0.0.1:53053. The persistent
include `/usr/local/etc/dnsmasq.conf.d/vpn-orchestrator.conf` sends each service's
DNS requests through its selected route and populates the corresponding PF
alias from answers. Service rules precede the TV default. Plain DNS uses a
60-second maximum response TTL; encrypted DNS on port 853 is rejected for the TV.
The former all-LAN DNS redirect is now limited to the TV alias.

Classification is best effort. Shared CDN addresses can overlap, with precedence
Max, Netflix, Prime Video, Disney+. Broad shared domains such as cloudfront.net
are deliberately excluded. HTTPS encrypted DNS, cached addresses, IPv6 bypass
outside this IPv4 gateway, and new vendor domains need separate investigation
if observed. Service health confirms the route, not playback or provider VPN
acceptance. Apps may retain territory, DRM or VPN-error state after connections
are reset.

## Validation

Final Seerr CI passed all 173 tests, type checking, formatting, translation
checks and lint (zero errors; 19 existing warnings). Broker and router plugin
CI also passed. The Seerr and broker runtime revisions are pinned in their
respective manifests.

- Appliance validation passed; both tunnels passed DNS and independent country
  checks, returning US and GB; direct egress returned IL.
- Forwarded traffic through the real service rules returned IL / US / GB / US.
  Temporary probe destinations, source aliases and host routes were removed.
- Broker service switches completed in 1.5–2.6 seconds. A real desktop UI
  Reconnect TV request traversed Seerr, the broker and OPNsense in 727 ms.
- Browser checks passed on desktop and 390px mobile, with correct selected
  values and no JavaScript page errors. Repeated against the final deployed
  image, including a browser-only simulated default outage: service controls
  remained enabled and unavailable routes were clearly marked.
- With the LG on, actual Max TCP traffic used direct NAT (10.100.102.254),
  while Netflix background TCP traffic used US tunnel NAT (10.2.0.2).
  DNS interception and alias learning were visible in the packet capture.
  A stale Max TCP connection received a reset after the reconnect action.
- No TV-originated IPv6 packets were observed in a short passive sample;
  this is not proof that the TV can never use IPv6.
- Actual application playback requires the user's confirmation.

## Recovery and upgrades

The appliance backup is `/root/vpn-routing-backup-20260910/`; it contains the
matching original configuration and scripts. Do not put the XML backup or API
credentials in this repository. Follow the plugin's
[provisioning and recovery instructions](https://github.com/alexfirilov/opnsense-vpn-orchestrator-plugin/blob/master/docs/service-routing-design.md)
for installation or rollback. Restoring the entire old configuration also
reverts unrelated changes made afterwards, so compare it first.

After an OPNsense upgrade, check the manual plugin files, persistent dnsmasq
include, external aliases, both tunnel handshakes, gateway/DNS host routes,
and `configctl vpn_orchestrator validate`. Recheck route status in Seerr.
