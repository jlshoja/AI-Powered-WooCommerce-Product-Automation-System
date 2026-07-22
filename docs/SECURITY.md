# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅        |
| 0.1.x   | ✅        |

## Reporting a Vulnerability

Email: security@yourdomain.com

Include:
- Description
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

Response time: 48 hours

---

## Security Measures Implemented

### Secrets Management
- **No secrets in code**: All credentials via `.env` (gitignored)
- **Template provided**: `.env.example` with placeholders
- **Settings loaded**: `config/settings.yaml` uses `${ENV_VAR}` placeholders
- **Python-dotenv**: Loads `.env` at startup in `main.py`
- **External Credentials**: API keys can be stored in external `providers.xlsx` (outside project root)
- **WooCommerce credentials**: Always in settings.yaml only (not in Excel)

### Input Validation
- **Pydantic models**: All data structures validated on parse
- **Excel parser**: Coerces types, handles NaN/None
- **Validator module**: Rules for required fields, SKU uniqueness, price ranges, stock, images, categories, attributes
- **Image validation**: Format (JPEG/PNG/WEBP), size (≤2MB), no executable content

### API Security
- **WooCommerce REST API**: Consumer Key/Secret auth (no OAuth tokens stored)
- **Retry logic**: Exponential backoff, no credential logging
- **Rate limiting**: ✅ **Implemented v0.2** - Token bucket algorithm
  - WooCommerce API: 1 req/s (configurable)
  - OpenAI API: 3 req/s burst 5 (configurable)
  - Handles 429 responses with exponential backoff
- **AI Provider Fallback**: ✅ **Implemented v0.3** - Multiple providers with automatic fallback
  - If primary provider fails → tries next provider
  - All providers exhausted → AI disabled, import continues
  - API key validated at startup (logs clearly if invalid)
- **External Credentials**: ✅ **Implemented v0.3** - API keys from external Excel file
  - Keeps secrets outside project root
  - WooCommerce credentials stay in settings.yaml only

### Image Handling
- **Download**: `requests` with timeout, stream to disk
- **Validate**: PIL checks format/magic bytes, size limit
- **Upload**: Multipart to WP media endpoint
- **SSRF Protection**: ✅ **Implemented v0.2** - Blocks private IP ranges:
  - 10.0.0.0/8
  - 172.16.0.0/12
  - 192.168.0.0/16
  - 127.0.0.0/8
  - 169.254.0.0/16
  - ::1/128, fc00::/7, fe80::/10
  - localhost, 0.0.0.0

### Content Security
- **HTML Sanitization**: ✅ **Implemented v0.2** - All AI-generated content sanitized with `bleach`
  - Allowed tags: p, br, strong, em, u, b, i, ul, ol, li, span, div
  - Allowed attributes: class, style on span/div
  - Strips dangerous tags (script, iframe, onload, etc.)

### Logging
- **No secrets in logs**: Credentials filtered
- **Structured**: Timestamp, logger, level, message
- **File rotation**: Not yet implemented

---

## Known Gaps & Roadmap

| Issue | Severity | Target |
|-------|----------|--------|
| No audit logging | Low | v0.3 |
| No file rotation for logs | Low | v0.3 |
| No dependency scanning | Low | v0.2 (Dependabot) |
| No async/await (scalability) | Medium | v0.3 |

---

## Threat Model

### Assets
- WooCommerce store (products, orders, customers)
- OpenAI API key
- Excel product data

### Attack Vectors
| Vector | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Credential leak via repo | High (was critical) | Critical | `.env` gitignored, `.env.example` only, `settings.yaml` gitignored |
| Malicious Excel upload | Medium | High | Pydantic validation, type coercion |
| SSRF via image URL | Medium | Medium | **Mitigated v0.2** - Private IP blocking |
| XSS via product description | Medium | Medium | **Mitigated v0.2** - Bleach sanitization |
| API rate limit abuse | Low | Medium | **Mitigated v0.2** - Token bucket rate limiting |
| AI provider failure | Low | Low | **Mitigated v0.3** - Automatic fallback to other providers |
| API key compromise | Medium | Medium | **Mitigated v0.3** - External credentials file, validation at startup |
| Dependency vulnerability | Low | Varies | Not yet scanned |

### Trust Boundaries
```
[Excel File] → [Parser] → [Validator] → [AI] → [WC API]
                    ↓           ↓
               [Local FS]  [OpenAI]
```
- Excel file: Untrusted (external source)
- Parser/Validator: Trusted (our code)
- Local FS: Trusted (our server)
- OpenAI: Semi-trusted (external API)
- WC API: Trusted (our store)

---

## Secure Development Practices

### For Contributors
1. Never commit `.env` or `settings.yaml` with real credentials
2. Run `ruff check` and `mypy` before PR
3. Add tests for new validation rules
4. Use parameterized queries (not applicable - REST API)
5. Sanitize user-facing output (descriptions, titles)

### Dependencies
- Pin versions in `pyproject.toml`
- Run `pip-audit` or `pip check` periodically
- Enable Dependabot alerts on GitHub

### Deployment
- Use separate WC API keys per environment (dev/staging/prod)
- Rotate keys quarterly
- Monitor WC API logs for anomalies
- Backup before bulk imports

---

## Incident Response

### Credential Compromise
1. Revoke compromised WC keys immediately
2. Generate new keys in WC → Settings → Advanced → REST API
3. Update `.env` and redeploy
4. Audit WC logs for unauthorized access
5. Rotate OpenAI key if exposed

### Data Corruption
1. Stop import process
2. Check `output/reports/import_report.xlsx` for failures
3. Use WC API to delete orphaned products (by SKU)
4. Re-run with corrected data

### Security Breach
1. Contain: Revoke keys, stop services
2. Assess: Check logs, API access history
3. Notify: Stakeholders, users if PII exposed
4. Remediate: Patch vulnerability, rotate all secrets
5. Review: Update threat model, add tests

---

## Configuration Reference

### CLI Flags
```bash
python -m src.main --test-sku 2106          # Test single product
python -m src.main --dry-run                # Validate only
python -m src.main --batch-size 20          # Custom batch size
python -m src.main --credentials providers.xlsx  # External API keys
```

### Rate Limiting (config/settings.yaml)
```yaml
woocommerce:
  rate_limit_rps: 1.0    # Requests per second
  rate_burst: 2          # Burst capacity

ai:
  rate_limit_rps: 3.0    # Requests per second
  rate_burst: 5          # Burst capacity
```

### SSRF Protection
```yaml
image:
  ssrf_protection: true  # Enable/disable
```

### HTML Sanitization
Automatic on all AI-generated fields. Uses bleach with safe tag allowlist.

---

*Last updated: 2026-07-22 (v0.3.0 - AI fallback, external credentials, CLI improvements)*