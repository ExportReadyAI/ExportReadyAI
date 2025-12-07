# Railway Deployment - Quick Reference

## 🚀 Quick Deploy Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare Railway deployment"
   git push origin main
   ```

2. **Login to Railway**
   - Go to [railway.app](https://railway.app)
   - Connect GitHub account

3. **Create Project**
   - New Project → Deploy from GitHub
   - Select `ExportReadyAI` repository

4. **Add Database**
   - Click "+ New" → Database → PostgreSQL
   - Railway auto-configures `DATABASE_URL`

5. **Set Environment Variables** (minimum required):
   ```
   SECRET_KEY=<generate-secure-key>
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   ALLOWED_HOSTS=.railway.app
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
   ```

6. **Deploy & Wait**
   - Railway builds automatically
   - Migrations run on startup
   - Get your URL from Domains tab

---

## 🔑 Generate SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 📝 Essential Environment Variables

```bash
# Core (Required)
SECRET_KEY=<your-secret-key>
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app
DATABASE_URL=<auto-injected-by-railway>

# Authentication (Required)
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
ADMIN_REGISTRATION_CODE=<your-admin-code>

# CORS (Required - Update with your frontend)
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CORS_ALLOW_ALL_ORIGINS=False

# AI Service (Required)
KOLOSAL_API_KEY=<your-kolosal-key>
KOLOSAL_BASE_URL=https://api.kolosal.ai/v1
KOLOSAL_MODEL=Claude Sonnet 4.5

# Storage (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<your-supabase-key>
SUPABASE_STORAGE_BUCKET=educational-materials
SUPABASE_CATALOG_BUCKET=catalog-images

# Monitoring (Optional but recommended)
SENTRY_DSN=<your-sentry-dsn>
```

---

## 🧪 Quick Verification

```bash
# Test health endpoint
curl https://your-project.up.railway.app/api/v1/health/

# Test API docs
curl https://your-project.up.railway.app/api/v1/docs/

# View logs
railway logs
```

---

## 🔧 Common Commands

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# View variables
railway variables

# Run migrations
railway run python manage.py migrate

# View logs
railway logs --follow

# Deploy manually
railway up
```

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Migration errors | `railway run python manage.py migrate` |
| Static files 404 | Check WhiteNoise middleware installed |
| CORS errors | Update `CORS_ALLOWED_ORIGINS` |
| 502 Bad Gateway | Check `railway logs` for startup errors |
| Database connection | Verify `DATABASE_URL` exists |

---

## 📚 Full Documentation

See **[RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md)** for detailed instructions.

---

**Support**: [Railway Discord](https://discord.gg/railway) | [Docs](https://docs.railway.app)
