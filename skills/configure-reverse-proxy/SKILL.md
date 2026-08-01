---
name: configure-reverse-proxy
description: Configure or audit Nginx as the public reverse proxy for a Docker Compose application on a single server. Use when deployment needs HTTP routing, HTTPS redirection, WebSockets, forwarded headers, upload limits, proxy timeouts, TLS certificate guidance, or safe Nginx configuration validation.
---

# Configure Reverse Proxy

Expose only the intended application entry point while keeping internal services private.

## Workflow

1. Require the analyzed domain, application upstream, public paths, WebSocket needs, upload limit, and timeout requirements.
2. Inspect existing proxy and TLS architecture before changing it.
3. Read [references/nginx-tls.md](references/nginx-tls.md).
4. Adapt [assets/default.conf.template](assets/default.conf.template) rather than copying it blindly.
5. Keep private keys and issued certificates outside the repository and mount them read-only.
6. Validate syntax with `nginx -t` in the target environment or an equivalent local container.
7. Document HTTP bootstrap, certificate issuance, renewal, safe reload, and rollback.

Obtain explicit approval immediately before changing live TLS, issuing certificates against a real domain, opening firewall ports, or reloading a production proxy.
