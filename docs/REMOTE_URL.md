# Remote ontology inspection (v0.3.0 development)

SemanticAudit accepts a local RDF document or an HTTP(S) URL as the input of `inspect`.
The command downloads the remote document into a temporary file, parses it,
and applies the same inspection rules used for local files. The temporary
file is deleted when inspection completes.

## Examples

```powershell
uv run python -m semantic_audit inspect `
  "https://raw.githubusercontent.com/w3c-lbd-cg/bot/master/bot.ttl" `
  --output reports/bot.json

uv run python -m semantic_audit inspect `
  "https://purl.obolibrary.org/obo/foodon.owl" `
  --rdf-format xml `
  --output reports/foodon.json
```

The format is detected using the server's supported RDF `Content-Type` or
the final URL's extension. If detection fails, supply `--rdf-format`.
Use the raw source URL, not the HTML `github.com/.../blob/...` page.

## Limitations and security

- Only HTTP(S) URLs are accepted. Requests follow HTTP redirects.
- The maximum response size is 100 MiB; network operations have a 30-second socket timeout.
- The original URL is preserved in the report's `source` field.
- The tool does **not** resolve `owl:imports` automatically.
- RDF parsers may independently fetch remote JSON-LD contexts or reference
  external resources. Inspect only sources you trust.
- This implementation is designed for **local CLI use**, not for arbitrary
  user-provided URLs in a hosted service. Before exposing this in a web API,
  add comprehensive SSRF defenses: block private and loopback IPs after DNS
  resolution, revalidate every redirect, enforce network egress restrictions,
  and control content decompression and other parser side effects.
- Live network integration tests must be run separately; the included unit
  tests simulate HTTP responses and do not depend on external servers.
