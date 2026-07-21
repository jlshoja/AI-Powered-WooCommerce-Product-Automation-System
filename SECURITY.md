# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
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

### Input Validation
- **Pydantic models**: All data structures validated on parse
- **Excel parser**: Coerces types, handles NaN/None
- **Validator module**: Rules for required fields, SKU uniqueness, price ranges, stock, images, categories, attributes
- **Image validation**: Format (JPEG/PNG/WEBP), size (≤2MB), no executable content

### API Security
- **WooCommerce REST API**: Consumer Key/Secret auth (no OAuth tokens stored)
- **Retry logic**: Exponential backoff, no credential logging
- **Rate limiting**: Not yet implemented (see Roadmap)

### Image Handling
- **Download**: `requests` with timeout, stream to disk
- **Validate**: PIL checks format/magic bytes, size limit
- **Upload**: Multipart to WP media endpoint
- **No SSRF protection**: URLs accepted as-is (see Roadmap)

### Logging
- **No secrets in logs**: Credentials filtered
- **Structured**: Timestamp, logger, level, message
- **File rotation**: Not yet implemented

---

## Known Gaps & Roadmap

| Issue | Severity | Target |
|-------|----------|--------|
| No rate limiting (WC API / OpenAI) | Medium | v0.2 |
| No SSRF protection on image URLs | Medium | v0.2 |
| No HTML sanitization (XSS in descriptions) | Medium | v0.2 |
| No audit logging | Low | v0.3 |
| No file rotation for logs | Low | v0.3 |
| No dependency scanning | Low | v0.2 (Dependabot) |

---

## Threat Model

### Assets
- WooCommerce store (products, orders, customers)
- OpenAI API key
- Excel product data

### Attack Vectors
| Vector | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Credential leak via repo | High (was critical) | Critical | `.env` gitignored, `.env.example` only |
| Malicious Excel upload | Medium | High | Pydantic validation, type coercion |
| SSRF via image URL | Medium | Medium | Not yet mitigated |
| XSS via product description | Medium | Medium | Not yet sanitized |
| API rate limit abuse | Low | Medium | Not yet limited |
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