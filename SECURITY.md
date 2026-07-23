# 🔒 Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Fully supported |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Aegis, please follow these steps:

1. **DO NOT** open a public GitHub issue — vulnerabilities should be reported privately
2. **Email** the details to **jadhavprathmesh042@gmail.com**
3. Include the following information:
   - Short description of the vulnerability
   - Steps to reproduce
   - Affected versions
   - Potential impact
   - Any suggested fix (if available)

### What to expect

- **Acknowledgment** within 48 hours of your report
- **Update** on the investigation within 5 business days
- **Fix timeline** communicated once the vulnerability is confirmed
- **Credit** in release notes when the fix is published (if you'd like)

## Security Best Practices for Users

### API Key Management
- Store your API keys in environment variables or a `.env` file (never commit them)
- Use the `.env.example` template as a guide — never fill in real secrets there
- Rotate keys periodically

### Docker Deployment
- Keep your Docker images and dependencies updated
- Run containers with minimal required privileges
- Use Docker's built-in security features (seccomp, AppArmor)
- Regularly scan images for known vulnerabilities

### Network Security
- Deploy behind a reverse proxy (nginx, Traefik) for TLS termination
- Restrict API access to trusted networks using firewall rules
- Enable authentication for the Streamlit dashboard in production

### Dependencies
- We use automated dependency scanning via GitHub Dependabot
- Keep `pip install -e ".[dev]"` up to date
- Review dependency changes before updating in production

## Known Security Considerations

- The application uses OpenAI-compatible API calls — ensure your API keys are stored securely
- Vector databases may contain sensitive incident data — encrypt at rest in production
- The dashboard is intended for internal use — add authentication for public deployments

## Vulnerability Disclosure Timeline

We aim to follow responsible disclosure:

1. **Report received** — we acknowledge and investigate
2. **Patch developed** — we create and test a fix
3. **Patch released** — we publish a new version with the fix
4. **Public disclosure** — we publish a security advisory (if warranted), typically 30+ days after the fix is available

---

**Thank you for helping keep Aegis and its community safe!** 🛡️

