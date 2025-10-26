# Security Guide

## Environment Variables & Credentials

### Overview

All sensitive credentials and configuration are stored in `.env` files, which are **never committed to version control**. This follows security best practices and prevents accidental credential leaks.

### File Structure

```
.env.example      # Template with placeholder values (SAFE to commit)
.env              # Actual credentials (NEVER commit - gitignored)
frontend/.env.example  # Frontend-specific template
```

### Setup Process

#### 1. First-Time Setup

When cloning the repository, you'll need to create your `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit the file with your actual credentials
nano .env  # or use your preferred editor
```

#### 2. Update Credentials

**CRITICAL**: Change the default database password immediately!

```bash
# In .env, change:
POSTGRES_PASSWORD=profits123_change_me_in_production
DATABASE_URL=postgresql://trader:YOUR_NEW_PASSWORD@postgres:5432/portfolio
```

**For production**, use a strong password:
- Minimum 20 characters
- Mix of uppercase, lowercase, numbers, symbols
- Generated with a password manager

Example strong password generator:
```bash
openssl rand -base64 32
```

#### 3. Anthropic API Key (for AI Features)

To use Epic 8 (AI Market Analysis), you need an Anthropic Claude API key:

1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Add to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here
```

**Note**: The app works fine without this key - AI features will just be disabled.

### What's Protected

The `.env` file contains:

1. **Database Credentials**
   - `POSTGRES_PASSWORD` - Database password
   - `DATABASE_URL` - Full connection string with password

2. **API Keys**
   - `ANTHROPIC_API_KEY` - Claude AI API key (cost: ~$0.06/day)

3. **Configuration**
   - All other settings are non-sensitive but kept in `.env` for consistency

### Git Protection

`.gitignore` is configured to **never commit** these files:

```gitignore
# Environment
.env
*.env
```

**Double-check before committing**:
```bash
git status
# .env should NOT appear in the list
# If it does, DO NOT COMMIT!
```

### Docker Compose Integration

`docker-compose.yml` references `.env` automatically:

```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Reads from .env
  DATABASE_URL: ${DATABASE_URL}
```

Default values are provided with `:-` syntax:
```yaml
ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}  # Empty string if not set
```

### Rotating Credentials

If credentials are compromised:

1. **Database Password**:
```bash
# Update .env with new password
POSTGRES_PASSWORD=new_secure_password_here
DATABASE_URL=postgresql://trader:new_secure_password_here@postgres:5432/portfolio

# Restart services
docker-compose down -v  # -v removes old data
docker-compose up
```

2. **Anthropic API Key**:
```bash
# Revoke old key at https://console.anthropic.com/
# Create new key
# Update .env
ANTHROPIC_API_KEY=sk-ant-api03-new-key-here

# Restart backend only
docker-compose restart backend
```

### Development vs Production

**Development** (current setup):
- Uses `.env` in repository root
- Weak password acceptable for local testing
- Services accessible on localhost

**Production** (future deployment):
- Use environment variables from hosting platform (e.g., Heroku, Railway, AWS)
- Strong passwords mandatory
- Secrets management service (AWS Secrets Manager, HashiCorp Vault)
- SSL/TLS for all connections
- Firewall rules limiting database access

### Security Checklist

- [x] `.env` is in `.gitignore`
- [x] `.env.example` has placeholder values only
- [x] No credentials hardcoded in source code
- [x] `docker-compose.yml` uses environment variables
- [ ] Strong database password (change from default!)
- [ ] Anthropic API key added (when ready for AI features)
- [ ] Regular credential rotation (every 90 days recommended)

### Emergency: Credentials Committed to Git

If you accidentally commit `.env`:

```bash
# 1. Remove from git immediately
git rm .env --cached
git commit -m "Remove accidentally committed .env file"

# 2. Rotate ALL credentials in the file
# (Change database password, API keys, etc.)

# 3. If pushed to GitHub, consider the credentials compromised
# - Rotate immediately
# - If public repo, use git-filter-branch to remove from history
```

### Questions?

- **Q**: What if I lose my `.env` file?
- **A**: Copy `.env.example` again and reconfigure. Database data persists in Docker volumes.

- **Q**: Can I share `.env` with team members?
- **A**: Only via secure channels (1Password, encrypted email). Never commit or send plain text.

- **Q**: How do I know if `.env` is loaded?
- **A**: Check container logs: `docker-compose logs backend | grep POSTGRES`

---

**Remember**: Security is a practice, not a feature. Treat credentials like house keys - keep them secret, rotate them regularly, and never leave them lying around!
