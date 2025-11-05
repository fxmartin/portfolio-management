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

#### 4. Alpha Vantage API Key (for Market Data Fallback)

To enable Alpha Vantage as a fallback for market data (especially for European ETFs), you need an Alpha Vantage API key:

1. Sign up at https://www.alphavantage.co/support/#api-key
2. Get your free API key (5 calls/minute, 100 calls/day)
3. Add to `.env`:
```bash
ALPHA_VANTAGE_API_KEY=YOUR_API_KEY_HERE
ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE=5    # Free tier limit
ALPHA_VANTAGE_RATE_LIMIT_PER_DAY=100     # Free tier limit
```

**Rate Limits**:
- **Free Tier**: 5 API calls per minute, 100 per day
- **Premium Tiers**: Higher limits available at https://www.alphavantage.co/premium/
- The app intelligently uses Yahoo Finance first (free, no limits) and falls back to Alpha Vantage only when needed

**When it's used**:
- Fallback when Yahoo Finance fails or returns no data for US stocks
- Cryptocurrency price fetching as alternative data source
- Circuit breaker pattern prevents excessive calls (opens after 5 failures, 5-min timeout)

**Monitoring API Usage**:
- Check usage statistics: `GET /monitoring/market-data`
- Alerts when approaching limits (80% of daily quota)
- Provider success rates and circuit breaker status

**Important Note**: Alpha Vantage **does not** have better European ETF coverage than Yahoo Finance. Both struggle with European exchanges (`.BE`, `.PA`, etc.). Your Yahoo Finance + `ETF_MAPPINGS` setup already handles European ETFs correctly.

**Note**: The app works fine without this key - Yahoo Finance handles most symbols. Alpha Vantage provides additional reliability for US stocks and crypto fallback.

### What's Protected

The `.env` file contains:

1. **Database Credentials**
   - `POSTGRES_PASSWORD` - Database password
   - `DATABASE_URL` - Full connection string with password

2. **API Keys**
   - `ANTHROPIC_API_KEY` - Claude AI API key (cost: ~$0.06/day)
   - `ALPHA_VANTAGE_API_KEY` - Market data API key (free tier: 100 calls/day)

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

### Settings Encryption Key (Epic 9)

As of Epic 9, sensitive settings (API keys, secrets) stored in the database are **encrypted at rest** using Fernet symmetric encryption.

#### 5. Settings Encryption Key Setup

Generate a secure encryption key for sensitive settings:

```bash
# Generate a new Fernet encryption key (44 characters)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
SETTINGS_ENCRYPTION_KEY=your_generated_encryption_key_here
```

**CRITICAL SECURITY NOTES**:
- ⚠️ **Keep this key secure!** If lost, encrypted settings **cannot be recovered**.
- 🔒 Never commit this key to version control
- 💾 Backup this key securely (1Password, encrypted vault, secure notes)
- 🔄 Rotate this key every 90 days (see rotation guide below)
- 📝 Document key location in your team's security procedures

**What's Encrypted**:
- `anthropic_api_key` - Claude AI API key
- `alpha_vantage_api_key` - Market data API key
- Any future API keys added to settings

**How It Works**:
1. When you save an API key in Settings UI → encrypted before storage
2. When you view a setting → decrypted only if `reveal=true` (masked by default)
3. When backend uses API key → automatically decrypted for use
4. Database backups contain encrypted values (safe to store)

**Key Recovery**:
- If key is lost: You must re-enter all API keys in Settings UI
- Database values remain encrypted but inaccessible
- **Prevention**: Store key in secure password manager immediately

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

3. **Alpha Vantage API Key**:
```bash
# Get new key at https://www.alphavantage.co/support/#api-key
# Update .env
ALPHA_VANTAGE_API_KEY=new_key_here

# Restart backend
docker-compose restart backend

# Check monitoring to verify
curl http://localhost:8000/monitoring/market-data
```

4. **Settings Encryption Key** (Advanced):

If your encryption key is compromised or you need to rotate it for compliance:

```bash
# 1. Generate a new encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Backup your database first!
make backup  # or: docker-compose exec postgres pg_dump -U trader portfolio > backup.sql

# 3. Run the key rotation utility
cd backend
python rotate_encryption_key.py \
    "OLD_KEY_HERE" \
    "NEW_KEY_HERE"

# The script will:
# - Validate both keys
# - Decrypt all sensitive settings with old key
# - Re-encrypt with new key
# - Verify successful rotation
# - Prompt you to update .env

# 4. Update .env with new key
nano .env
# Change: SETTINGS_ENCRYPTION_KEY=NEW_KEY_HERE

# 5. Restart backend
docker-compose restart backend

# 6. Verify settings are accessible
curl http://localhost:8000/api/settings/category/api_keys
```

**Key Rotation Safety**:
- ✅ Atomic transaction - all settings rotate or none (no partial state)
- ✅ Verification step confirms all settings decrypt with new key
- ✅ Rollback if any errors occur
- ✅ Database backup recommended before rotation
- ⚠️ Downtime: ~10 seconds during rotation (settings unavailable)

**Rotation Schedule**:
- Every 90 days for compliance
- Immediately if key is compromised
- Before major production deployments

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
