# Security Policy

## Supported Versions

We actively support the following versions of Codebase CSI with security updates:

| Version | Supported          | End of Life    |
| ------- | ------------------ | -------------- |
| 1.0.x   | :white_check_mark: | TBD            |
| < 1.0   | :x:                | November 2025  |

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

We take security seriously. If you discover a security vulnerability in Codebase CSI, please report it privately.

### How to Report

Send an email to: **security@codebase-csi.com**

Include the following information:

1. **Description** - Detailed description of the vulnerability
2. **Impact** - Potential impact and attack scenarios
3. **Reproduction Steps** - Step-by-step instructions to reproduce
4. **Proof of Concept** - Code, screenshots, or videos demonstrating the issue
5. **Affected Versions** - Which versions are affected
6. **Suggested Fix** - If you have ideas for a fix (optional)
7. **Your Contact Info** - For follow-up questions

### Example Report

```
Subject: [SECURITY] SQL Injection in Pattern Analyzer

Description:
The pattern analyzer's regex matching allows SQL injection when 
processing specially crafted file names.

Impact:
An attacker could execute arbitrary SQL commands by creating files 
with malicious names, potentially compromising the database.

Steps to Reproduce:
1. Create file named: `'; DROP TABLE users; --`
2. Run: csi scan .
3. Observe SQL injection in logs

Affected Versions:
1.0.0 - 1.0.5

Suggested Fix:
Sanitize file names before using in SQL queries.
Use parameterized queries instead of string concatenation.

Contact: researcher@example.com
```

---

## Response Timeline

We aim to respond to security reports according to the following timeline:

| Stage | Timeline |
|-------|----------|
| **Initial Response** | Within 24 hours |
| **Vulnerability Assessment** | Within 72 hours |
| **Fix Development** | Within 7 days (for critical issues) |
| **Security Patch Release** | Within 14 days |
| **Public Disclosure** | 30 days after patch release |

### Severity Levels

**Critical** (CVSS 9.0-10.0)
- Remote code execution
- Authentication bypass
- Data breach

**High** (CVSS 7.0-8.9)
- SQL injection
- Cross-site scripting (XSS)
- Privilege escalation

**Medium** (CVSS 4.0-6.9)
- Information disclosure
- Denial of service
- Insecure dependencies

**Low** (CVSS 0.1-3.9)
- Minor information leaks
- Configuration issues

---

## What to Expect

### 1. Acknowledgment

We'll acknowledge receipt of your report within 24 hours and provide:
- A unique tracking ID for your report
- Expected timeline for assessment
- Contact person for follow-up

### 2. Assessment

Our security team will:
- Verify the vulnerability
- Assess severity using CVSS scoring
- Determine affected versions
- Develop a remediation plan

### 3. Fix Development

We'll:
- Develop and test a security patch
- Create a security advisory
- Prepare release notes

### 4. Release

We'll:
- Release the security patch
- Publish the security advisory (CVE if applicable)
- Notify affected users
- Credit the reporter (unless anonymity is requested)

### 5. Disclosure

After 30 days (or when 95% of users have updated):
- Full details published in security advisory
- CVE assigned if applicable
- Technical write-up published

---

## Security Best Practices

### For Users

**Keep Updated**
```bash
pip install --upgrade codebase-csi
```

**Use Virtual Environments**
```bash
python -m venv .venv
source .venv/bin/activate
pip install codebase-csi
```

**Verify Package Integrity**
```bash
pip install codebase-csi --require-hashes
```

**Review Scan Reports**
- Don't ignore security warnings
- Act on HIGH/CRITICAL findings
- Keep audit logs

**Secure Your Config**
```yaml
# csi-config.yaml
# Don't commit secrets!
api_keys: ${API_KEY}  # Use environment variables
database_url: ${DATABASE_URL}
```

### For Contributors

**Secure Coding Practices**
- Input validation
- Parameterized queries
- Proper error handling
- Secure defaults
- Least privilege principle

**Dependency Management**
```bash
# Check for known vulnerabilities
pip install safety
safety check

# Keep dependencies updated
pip install --upgrade -r requirements.txt
```

**Code Review**
- Security-focused review for PRs
- Static analysis with bandit
- Dependency scanning with dependabot

---

## Known Security Issues

### Current Issues

*None at this time*

### Resolved Issues

#### CVE-2025-XXXXX (Example - Not real)
**Severity**: High (CVSS 7.5)  
**Affected**: 1.0.0 - 1.0.3  
**Fixed**: 1.0.4  
**Description**: Path traversal in file scanner  
**Mitigation**: Upgrade to 1.0.4 or later

---

## Security Advisories

Subscribe to security advisories:

- **GitHub**: Watch repository → Custom → Security alerts
- **Email**: security-announce@codebase-csi.com (send "subscribe")
- **RSS**: https://github.com/codebase-csi/codebase-csi/security/advisories.atom

---

## Bug Bounty Program

### Scope

**In Scope**:
- Remote code execution
- SQL injection
- Authentication bypass
- Data exfiltration
- Privilege escalation

**Out of Scope**:
- Social engineering
- Physical attacks
- DoS attacks (unless trivial to execute)
- Issues in dependencies (report to upstream)
- Already-known issues

### Rewards

| Severity | Reward |
|----------|--------|
| Critical | $1,000 |
| High     | $500   |
| Medium   | $250   |
| Low      | $100   |

**Additional Rewards**:
- Public recognition (Hall of Fame)
- Codebase CSI swag
- Early access to new features

### Rules

- Don't access or modify user data
- Don't disrupt the service
- Don't publicly disclose before patch
- One reward per unique vulnerability
- First reporter gets the reward

---

## Security Contacts

### General Security
**Email**: security@codebase-csi.com  
**PGP Key**: [Download](https://codebase-csi.com/security.asc)

### Bug Bounty
**Email**: bounty@codebase-csi.com

### Security Team
- **Lead**: security-lead@codebase-csi.com
- **Response Team**: incident@codebase-csi.com

---

## Compliance & Certifications

Codebase CSI follows:

- OWASP Top 10
- CWE Top 25
- SANS Top 25
- NIST Cybersecurity Framework

---

## Third-Party Dependencies

We actively monitor dependencies for vulnerabilities using:

- GitHub Dependabot
- Safety (Python)
- Snyk
- PyUp

View our dependency tree:
```bash
pip install pipdeptree
pipdeptree -p codebase-csi
```

---

## Responsible Disclosure

We believe in responsible disclosure:

1. **Private Reporting** → Report vulnerabilities privately first
2. **Coordinated Fix** → Work together on a fix
3. **Patch Release** → Release security patch
4. **Public Disclosure** → Disclose after users have time to update

We commit to:
- Responding promptly
- Keeping you informed
- Crediting you publicly (if desired)
- Not taking legal action against good-faith researchers

---

## Questions?

Have questions about our security policy?

**Email**: security@codebase-csi.com

---

**Last Updated**: November 23, 2025

Thank you for helping keep Codebase CSI and our users secure! 🔒
