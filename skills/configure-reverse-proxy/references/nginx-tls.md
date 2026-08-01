# Nginx and TLS

## Routing

- Resolve the application by its Compose service name on the private network.
- Forward `Host`, client address, forwarding chain, and original scheme.
- Support WebSocket upgrade only where needed.
- Set request-size and timeout values from application requirements rather than using unbounded defaults.
- Serve static files directly only when ownership and cache invalidation are defined.
- Expose only ports 80 and 443 from the proxy service.

## TLS lifecycle

1. Confirm DNS resolves to the intended server.
2. Validate an HTTP-only bootstrap configuration.
3. Obtain explicit approval before opening ports, requesting a real certificate, or changing live configuration.
4. Issue the certificate with a supported ACME client using repository-specific domain and contact placeholders.
5. Mount certificate material read-only and outside version control.
6. Validate `nginx -t` before every reload.
7. Test renewal with the ACME client's dry-run mode.
8. Document rollback to the last validated configuration.

Do not include real domains, email addresses, private keys, or certificate data in generated repository files.
