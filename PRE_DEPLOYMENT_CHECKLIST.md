# Pre-Deployment Checklist ✅

**Before deploying ClaimGuard V2 to production, verify all items below.**

---

## Security Checklist

- [x] **Test user seeding disabled in production** — Now only seeds in dev/test mode
- [x] **Error messages safe in production** — Errors don't leak internal details
- [x] **JWT secrets configured** — SECRET_KEY and JWT_SECRET_KEY in .env
- [x] **FLASK_DEBUG=False in production** — Debug mode disabled
- [x] **Database credentials secure** — Use strong passwords
- [x] **No hardcoded secrets in code** — All secrets in .env only

**Before deploying:**
- [ ] Generate new SECRET_KEY (32+ random characters)
- [ ] Generate new JWT_SECRET_KEY (32+ random characters)
- [ ] Set strong database password
- [ ] Enable HTTPS/SSL certificate
- [ ] Set FLASK_ENV=production in .env

---

## Functionality Checklist

- [x] **Phase 1: Dependencies** — All packages installed
- [x] **Phase 2: Infrastructure** — Config, storage, DB migration ready
- [x] **Phase 3: Document Intelligence** — OCR, extraction, classification working
- [x] **Phase 4: Document Validation** — Data quality, consistency, fraud detection working
- [x] **UX Redesign** — Human-friendly validation report
- [x] **Health Check Endpoint** — `/api/health` returns status
- [x] **Status Endpoint** — `/api/status` (auth required) shows system info
- [x] **Error Handlers** — Safe error responses in production

**Test locally:**
- [ ] Backend starts: `python app.py`
- [ ] Frontend loads: `npm start`
- [ ] Login works: `customer@test.com / password123`
- [ ] Document upload works
- [ ] OCR extracts text
- [ ] Validation scores correctly
- [ ] No errors in browser console (F12)
- [ ] No errors in backend logs

---

## Database Checklist

**For SQLite (simpler, development):**
- [ ] SQLite installed (usually included with Python)
- [ ] Database file location decided (`/var/claimguard/claimguard.db` recommended)
- [ ] Backup plan in place (daily backups)

**For PostgreSQL (recommended, production):**
- [ ] PostgreSQL installed (v12+)
- [ ] Database created: `createdb claimguard_prod`
- [ ] Database user created with secure password
- [ ] Connection string verified: `postgresql://user:pass@host:5432/claimguard_prod`
- [ ] Backup plan in place (daily automated backups)
- [ ] Connection pooling configured (pgBouncer recommended)

---

## Dependencies Checklist

**Python:**
- [ ] Python 3.8+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] spaCy model downloaded: `python -m spacy download en_core_web_sm`
- [ ] Poppler installed (for PDF processing)
  - Windows: `choco install poppler`
  - Mac: `brew install poppler`
  - Linux: `apt-get install poppler-utils`

**Node.js:**
- [ ] Node.js 14+ installed
- [ ] npm dependencies installed: `npm install`
- [ ] Frontend built: `npm run build`

---

## Configuration Checklist

**Environment Variables (.env):**
- [ ] FLASK_ENV=production
- [ ] FLASK_DEBUG=False
- [ ] SECRET_KEY set (32+ chars)
- [ ] JWT_SECRET_KEY set (32+ chars)
- [ ] SQLALCHEMY_DATABASE_URI set (correct database)
- [ ] FRONTEND_URL set (correct domain)
- [ ] LOG_LEVEL set (INFO for production)
- [ ] ENABLE_OCR=true
- [ ] ENABLE_ML_PREDICTIONS=true
- [ ] ENABLE_FRAUD_DETECTION=true

**Optional (for production):**
- [ ] EMAIL configuration (MAIL_SERVER, MAIL_PORT, etc.)
- [ ] AWS S3 configuration (if using cloud storage)
- [ ] Analytics enabled (if desired)

---

## Server Setup Checklist

**Networking:**
- [ ] Firewall configured (allow ports 80, 443)
- [ ] Port 5000 (backend) not exposed to internet (use reverse proxy)
- [ ] Port 3000 (frontend) served through web server (nginx, Apache)
- [ ] DNS configured (if using domain)

**Reverse Proxy (Nginx or Apache):**
- [ ] Backend proxied to http://localhost:5000
- [ ] Frontend served from build directory
- [ ] HTTPS/SSL configured
- [ ] Gzip compression enabled
- [ ] Cache headers configured

**Monitoring:**
- [ ] Logging configured (`/var/log/claimguard/`)
- [ ] Log rotation configured (logrotate)
- [ ] Health check endpoint monitored
- [ ] Uptime monitoring set up (optional)

---

## Production Services Checklist

**Backend:**
- [ ] Running with gunicorn (not dev server): `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
- [ ] Started as systemd service (for auto-restart)
- [ ] Environment variables loaded from .env
- [ ] Logging to file (not just stdout)

**Frontend:**
- [ ] Production build created: `npm run build`
- [ ] Served by web server (nginx, Apache, or `serve`)
- [ ] GZIP compression enabled
- [ ] Cache busting configured (webpack hashes)

**Database:**
- [ ] Automated backups scheduled
- [ ] Connection pooling configured (PostgreSQL)
- [ ] Maintenance tasks scheduled (vacuum, analyze)

---

## Testing Before Deployment

**Manual Testing:**
```bash
# Test 1: Health check
curl http://localhost:5000/api/health

# Test 2: Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'

# Test 3: Upload document
# Use frontend UI or API

# Test 4: Verify database
curl http://localhost:5000/api/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Frontend Testing:**
- [ ] Load homepage
- [ ] Login with test account
- [ ] Navigate all pages
- [ ] Upload document
- [ ] View validation report
- [ ] No console errors (F12)
- [ ] Responsive on mobile (browser resize)

**Stress Testing (optional):**
```bash
# Install Apache Bench: apt-get install apache2-utils
# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:5000/api/health
```

---

## Deployment Steps

### Step 1: Pre-flight
- [ ] All items above checked
- [ ] Backups created
- [ ] Rollback plan documented

### Step 2: Deploy Backend
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app &
```

### Step 3: Deploy Frontend
```bash
cd frontend
serve -s build -l 3000 &
# OR configure web server to serve 'build' directory
```

### Step 4: Verify Deployment
```bash
curl http://localhost:5000/api/health
curl http://localhost:3000  # Should load frontend
```

### Step 5: Monitor
- [ ] Check logs for errors
- [ ] Monitor health endpoint
- [ ] Monitor database connection
- [ ] Monitor disk space

---

## Post-Deployment Checklist

- [ ] Health check endpoint responds 200
- [ ] Frontend loads and is responsive
- [ ] Login works
- [ ] Can upload documents
- [ ] OCR processes documents
- [ ] Validation scoring works
- [ ] Errors logged to file
- [ ] Database backups automated
- [ ] Monitoring/alerting configured

---

## Rollback Plan

If something goes wrong:

**Quick Rollback (same version):**
```bash
# Restart services
systemctl restart claimguard-backend
systemctl restart claimguard-frontend
```

**Rollback to Previous Version:**
```bash
git checkout v2.0.0-beta  # Previous stable version
# Restart services
```

**Rollback to V1:**
```bash
git checkout v1-stable
# Restore V1 database backup
# Restart services
```

---

## Success Criteria

✅ All items checked  
✅ All tests passing  
✅ No errors in logs  
✅ Health endpoint responds  
✅ Frontend loads  
✅ Login works  
✅ OCR processes documents  
✅ Backups configured  

**You're ready to deploy!** 🚀

---

## Questions?

If anything fails, check:
1. `PRODUCTION_README.md` — Full deployment guide
2. `DEPLOYMENT_TROUBLESHOOTING.md` — Common issues and fixes
3. Backend logs: `tail -f /var/log/claimguard/app.log`
4. Frontend console: Browser F12 → Console tab

---

**Last Updated:** October 8, 2026  
**Version:** 2.0.0-MVP  
**Status:** Ready for Deployment ✅
