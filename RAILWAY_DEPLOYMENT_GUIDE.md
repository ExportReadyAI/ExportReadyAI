# 🚀 Railway Deployment Guide - ExportReady.AI

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your code to GitHub
3. **Supabase Account**: For PostgreSQL database (or use Railway PostgreSQL)

---

## 🔧 Step 1: Prepare Your Repository

Pastikan file-file berikut sudah ada di repository (sudah dibuat):

- ✅ `railway.json` - Railway configuration
- ✅ `Procfile` - Process definitions
- ✅ `nixpacks.toml` - Build configuration
- ✅ `runtime.txt` - Python version specification
- ✅ `requirements/production.txt` - Production dependencies

---

## 🗄️ Step 2: Setup Database (Option A: Railway PostgreSQL)

### Via Railway Dashboard:

1. Buka project Railway Anda
2. Klik **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway akan otomatis create database dan environment variable `DATABASE_URL`
4. Database siap digunakan! 🎉

### Via Railway CLI:

```bash
railway add --database postgresql
```

---

## 🗄️ Step 2 Alternative: Setup Database (Option B: Supabase)

Jika menggunakan Supabase PostgreSQL:

1. Login ke [Supabase Dashboard](https://supabase.com/dashboard)
2. Buat project baru atau gunakan existing
3. Copy **Database URL** dari:
   - Settings → Database → Connection String → URI
4. Format URL: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

---

## 🚂 Step 3: Deploy to Railway

### Method 1: Via Railway Dashboard (Recommended)

1. **Login ke Railway**
   - Buka [railway.app](https://railway.app)
   - Login dengan GitHub

2. **Create New Project**
   - Klik **"New Project"**
   - Pilih **"Deploy from GitHub repo"**
   - Select repository: `ExportReadyAI`
   - Railway akan detect Django dan auto-configure

3. **Add Database** (jika belum)
   - Klik **"+ New"** → **"Database"** → **"Add PostgreSQL"**

4. **Configure Environment Variables** (lihat Section Step 4)

5. **Deploy**
   - Railway akan otomatis build dan deploy
   - Tunggu hingga status menjadi **"Success"** ✅

### Method 2: Via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

---

## 🔐 Step 4: Configure Environment Variables

Di Railway Dashboard → **Variables**, tambahkan:

### Required Variables:

```bash
# Django Core
SECRET_KEY=your-super-secret-key-min-50-characters-recommended
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app

# Database (Railway PostgreSQL akan auto-inject DATABASE_URL)
# Jika pakai Supabase, set manual:
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# CORS Configuration (Update dengan frontend domain Anda)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,https://www.your-domain.com
CORS_ALLOW_ALL_ORIGINS=False

# SSL/Security (Railway provides HTTPS)
SECURE_SSL_REDIRECT=True

# Admin Registration
ADMIN_REGISTRATION_CODE=your-secure-admin-code-here

# Kolosal AI Configuration
KOLOSAL_API_KEY=your-kolosal-api-key
KOLOSAL_BASE_URL=https://api.kolosal.ai/v1
KOLOSAL_MODEL=Claude Sonnet 4.5

# Supabase Storage (untuk file uploads)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_STORAGE_BUCKET=educational-materials
SUPABASE_CATALOG_BUCKET=catalog-images
```

### Optional Variables:

```bash
# Sentry Monitoring (Optional tapi recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Logging Level
DJANGO_LOG_LEVEL=INFO

# Railway-specific (Auto-injected)
PORT=8000  # Railway auto-sets this
RAILWAY_STATIC_URL=your-url.railway.app
RAILWAY_PUBLIC_DOMAIN=your-domain.railway.app
```

---

## 🎯 Step 5: Get Your Deployment URL

Setelah deployment success:

1. **Find URL**:
   - Railway Dashboard → Settings → Domains
   - Default: `https://your-project.up.railway.app`

2. **Add Custom Domain** (Optional):
   - Settings → Domains → **"+ Add Domain"**
   - Input custom domain Anda
   - Update DNS records sesuai instruksi Railway

3. **Update Environment Variables**:
   ```bash
   ALLOWED_HOSTS=your-custom-domain.com,.railway.app,.up.railway.app
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain.com
   ```

---

## 🧪 Step 6: Verify Deployment

### Check Health Endpoint:

```bash
# Health check
curl https://your-project.up.railway.app/api/v1/health/

# API Documentation
curl https://your-project.up.railway.app/api/v1/docs/
```

### Check Logs:

**Via Dashboard:**
- Railway Dashboard → Deployments → View Logs

**Via CLI:**
```bash
railway logs
```

### Test API Endpoints:

```bash
# Test countries endpoint (no auth required)
curl https://your-project.up.railway.app/api/v1/countries/

# Test authentication
curl -X POST https://your-project.up.railway.app/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

---

## 🔄 Step 7: Setup Continuous Deployment

Railway automatically deploys on every push to `main` branch!

### Workflow:
1. Push code ke GitHub
2. Railway detects changes
3. Auto-build & deploy
4. Migrations run automatically
5. New version live! 🚀

### Disable Auto-Deploy (Optional):
- Dashboard → Settings → **"Auto Deployments"** → Toggle Off

---

## 🛠️ Troubleshooting

### Issue: Migration Errors

**Solution:**
```bash
# Via Railway CLI
railway run python manage.py migrate --noinput

# Via Dashboard
# Settings → Add this to Start Command:
python manage.py migrate --noinput && gunicorn config.wsgi:application
```

### Issue: Static Files Not Loading

**Check:**
1. WhiteNoise installed: `pip list | grep whitenoise`
2. Middleware configured di `settings/base.py`
3. `STATIC_ROOT` dan `STATICFILES_STORAGE` set correctly

**Fix:**
```bash
railway run python manage.py collectstatic --noinput
```

### Issue: Database Connection Errors

**Check:**
1. `DATABASE_URL` environment variable exists
2. Database service is running
3. SSL connection enabled di `production.py`

**Verify:**
```bash
railway variables
```

### Issue: CORS Errors

**Solution:**
```bash
# Update CORS_ALLOWED_ORIGINS di Railway Variables
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com

# Untuk development (NOT for production):
CORS_ALLOW_ALL_ORIGINS=True
```

### Issue: 502 Bad Gateway

**Possible causes:**
1. App not starting properly (check logs)
2. PORT environment variable not set
3. Gunicorn workers crashed

**Solution:**
```bash
# Check logs
railway logs

# Restart deployment
railway up --detach
```

---

## 📊 Monitoring & Logging

### View Logs:
```bash
# Real-time logs
railway logs --follow

# Specific deployment
railway logs --deployment-id <id>
```

### Setup Sentry (Recommended):

1. **Create Sentry Account**: [sentry.io](https://sentry.io)
2. **Create Django Project** di Sentry
3. **Copy DSN** dari Project Settings
4. **Add to Railway Variables**:
   ```bash
   SENTRY_DSN=https://your-dsn@sentry.io/project-id
   ```
5. Sentry akan auto-capture errors! 📈

---

## 🔒 Security Best Practices

### ✅ Checklist Sebelum Production:

- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY` (min 50 characters)
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] `CORS_ALLOWED_ORIGINS` specified (not allow all)
- [ ] SSL redirect enabled (`SECURE_SSL_REDIRECT=True`)
- [ ] Database SSL enabled
- [ ] Sentry error tracking setup
- [ ] Regular backups configured
- [ ] Environment variables secured (tidak di-commit ke Git)
- [ ] Admin registration code strong dan secure

### Generate Secure SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 📦 Database Backups

### Automated Backups (Railway):

Railway PostgreSQL includes automated daily backups!

**Restore from backup:**
1. Dashboard → Database → Backups
2. Select backup date
3. Click "Restore"

### Manual Backup (Supabase):

```bash
# Export database
pg_dump -h db.your-project.supabase.co -U postgres -d postgres > backup.sql

# Import database
psql -h db.your-project.supabase.co -U postgres -d postgres < backup.sql
```

---

## 🎓 Useful Railway Commands

```bash
# Link to existing project
railway link

# Show environment variables
railway variables

# Set environment variable
railway variables set KEY=value

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser

# Open Rails Console (interactive)
railway run python manage.py shell

# View service info
railway status

# Open in browser
railway open
```

---

## 📞 Support & Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Django Deployment**: [docs.djangoproject.com/en/5.0/howto/deployment/](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)

---

## ✅ Post-Deployment Checklist

- [ ] Backend deployed successfully
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Environment variables configured
- [ ] API endpoints responding correctly
- [ ] CORS properly configured for frontend
- [ ] Admin panel accessible
- [ ] Error monitoring (Sentry) active
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] Database backups verified
- [ ] Documentation updated with production URL

---

## 🚀 Next Steps

1. **Test All Endpoints** dengan production URL
2. **Update Frontend** dengan production API URL
3. **Setup Monitoring** dashboard (Sentry)
4. **Configure Alerts** untuk error monitoring
5. **Plan Scaling Strategy** jika traffic tinggi

---

**Deployment Success!** 🎉

Your ExportReady.AI backend is now live on Railway!

**Production URL**: `https://your-project.up.railway.app`

**API Docs**: `https://your-project.up.railway.app/api/v1/docs/`

---

*Last Updated: December 7, 2025*
