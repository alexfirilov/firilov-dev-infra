# assistant

The self-hosted personal assistant. The image and agent policy are in [alexfirilov/home-agent](https://github.com/alexfirilov/home-agent).

| Pod | What it does | Storage |
|---|---|---|
| `agent` | Claude Code (owner's subscription) in tmux, with the official Telegram channel. Tool approvals arrive in Telegram as Allow/Deny buttons | `agent-home` 20Gi: Claude login, plugins, memory, workspace |
| `browser` | Headful Chromium (linuxserver/chromium with Selkies) and a Playwright MCP sidecar on `:8931` that drives it over CDP | `browser-config` 5Gi: browser profile |
| `waha` | WhatsApp gateway (WAHA GOWS engine) with its built-in MCP at `/mcp` | `waha-sessions` 2Gi: the linked-device session |

**Access.** The owner reaches these over the tailnet only (`tailscale-ingress.yaml`); nothing goes through cloudflared:
- `https://agent-browser.<tailnet>.ts.net`: take over the browser (CAPTCHA/OTP). Basic auth: `BROWSER_USER/PASSWORD`.
- `https://agent-whatsapp.<tailnet>.ts.net/dashboard`: WAHA dashboard. Auth: `WAHA_DASHBOARD_USERNAME/PASSWORD`.

The plaintext credentials are in `~/work/private/assistant-credentials.txt` on k3s2 (mode 0600).

**Network.** `networkpolicy.yaml` limits all three pods to DNS and the public internet; private, CGNAT and link-local ranges are blocked. Only the agent can reach the browser MCP and WAHA, and only the tailscale namespace can reach the UIs.

## Operating
```bash
KC=~/work/private/openvpn-provisioner-kubeconfig
kubectl --kubeconfig $KC -n assistant exec -it deploy/agent -- tmux attach -t agent   # Ctrl-b d to detach
kubectl --kubeconfig $KC -n assistant logs deploy/waha
```

**Rules:**
- Every Deployment runs `replicas: 1` with `Recreate`. Never scale any of them. Two WAHA pods on one session risks a WhatsApp ban; two agents would fight over the Telegram bot.
- Losing `waha-sessions` means re-pairing the phone (WhatsApp, then Linked devices).
- Losing `agent-home` means redoing `/login` and Telegram pairing.
