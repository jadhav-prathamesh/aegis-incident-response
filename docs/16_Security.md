# Aegis — "Multi-Agent AI Incident Response Platform"
## Security

## Purpose

Document the current security posture, configuration, and gaps.

## Source Traceability

| Component | File |
|---|---|
| Security settings | `src/core/config.py:SecuritySettings` |
| CORS middleware | `src/api/app.py:37-43` |
| Exception handling | `src/core/exceptions.py:AuthenticationError` |
| Exception handling | `src/core/exceptions.py:AuthorizationError` |
| Secrets in config | `.env.example` (placeholders) |

## Current Security Implementation

### CORS Configuration

The FastAPI application has CORS middleware configured in `src/api/app.py:37-43`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=settings.security.cors_allow_methods,
    allow_headers=settings.security.cors_allow_headers,
)
```

Default allowed origins: `http://localhost:3000`, `http://localhost:8080`.

### Exception Classes

Two exception classes for security scenarios are defined but not wired into middleware:
- `AuthenticationError` (401) in `src/core/exceptions.py:40`
- `AuthorizationError` (403) in `src/core/exceptions.py:50`

## Security Settings (Configured but Not Wired)

The `SecuritySettings` class in `src/core/config.py:140-166` defines:

| Variable | Default | Purpose | Wired? |
|---|---|---|---|
| `SECURITY_SECRET_KEY` | "change-me-in-production" | JWT signing | No |
| `SECURITY_ALGORITHM` | HS256 | JWT algorithm | No |
| `SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token TTL | No |
| `SECURITY_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL | No |
| `SECURITY_API_KEY_HEADER` | X-API-Key | Header name | No |
| `SECURITY_RATE_LIMIT_REQUESTS` | 100 | Rate limit cap | No |
| `SECURITY_RATE_LIMIT_WINDOW_SECONDS` | 60 | Rate limit window | No |
| `SECURITY_ENCRYPTION_KEY` | None | Data encryption | No |
| `SECURITY_AUDIT_ENABLED` | true | Audit logging | Via structlog only |

## Security Gaps

The following security measures are **not implemented**:

| Gap | Impact | Source Evidence |
|---|---|---|
| **No authentication middleware** | API is publicly accessible | `src/api/app.py` — no auth middleware registered |
| **No JWT validation** | JWT config exists but never used | `SecuritySettings` defined, no `decode()` call |
| **No RBAC** | No role-based access control | No user/role models |
| **No rate limiting** | API vulnerable to DoS | `RateLimitError` exists but no middleware |
| **No input sanitization** | SQL injection risk in pgvector queries | `src/core/vector_db.py` — f-string table names |
| **No secrets management** | Secrets in .env with defaults | `.env.example` contains placeholder credentials |
| **Hardcoded passwords** | docker-compose defaults | `docker-compose.yml:32-33` — `postgres:postgres` |
| **No TLS** | All traffic in plaintext | No HTTPS configuration |
| **No audit middleware** | No request logging middleware | Only application-level logging via structlog |

## Best Practices

The codebase follows some security-conscious patterns:
- **Approval gates** — High-risk actions require approval before execution
- **Dry-run mode** — Actions can be executed in dry-run mode (controlled by `FEATURE_CHAOS_ENGINEERING`)
- **Structured logging** — All operations logged with context
- **Exception serialization** — `to_dict()` methods avoid leaking stack traces in API responses

## Recommendations for Production

1. Wire JWT authentication middleware with bearer token validation
2. Add API key authentication as an alternative
3. Implement rate limiting middleware
4. Add input validation and parameterized queries
5. Use a secrets manager (Vault, AWS Secrets Manager)
6. Configure HTTPS with proper certificates
7. Add audit middleware for request/response logging
8. Remove default credentials from docker-compose
9. Add CORS origin validation beyond wildcard methods
