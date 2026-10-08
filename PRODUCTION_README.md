# 🚀 ClaimGuard V2 — Production Deployment Guide

**Status:** ✅ Production Ready  
**Version:** 2.0.0-MVP  
**Date:** October 8, 2026  
**Branch:** `v2-dev`

---

## What You're Deploying

ClaimGuard V2 is a **production-grade insurance claim validation system** with:
- 🧠 **AI-powered document processing** (OCR, field extraction, classification)
- ✅ **Smart validation** (data quality, consistency, fraud detection)
- 🎨 **Human-friendly UI** (plain language, mobile-responsive)
- 🔒 **Production-ready infrastructure** (PostgreSQL, S3-ready, scalable)

---

## 60-Second Quick Start

### On Windows:
```bash
# 1. Run deployment script
DEPLOY.bat

# 2. Configure environment
copy backend\.env.example backend\.env
# Edit backend\.env (set database URL, secret keys)

# 3. Start backend
cd backend
python app.py

# 4. In another terminal, start frontend
cd frontend
npm start
```

### On Linux/Mac:
```bash
# 1. Run deployment script
chmod +x DEPLOY.sh
./DEPLOY.sh

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env (set database URL, secret keys)

# 3. Start backend
cd backend
python app.py

# 4. In another terminal, start frontend
cd frontend
npm start
```

**Then:** Open http://localhost:3000  
**Login:** `customer@test.com` / `password123`

---

## Full Deployment Guide

### Prerequisites

- **Python 3.8+**
- **Node.js 14+**
- **PostgreSQL 12+** (recommended) or SQLite (included)
- **1GB RAM minimum**

### Step 1: Clone & Checkout

```bash
git clone <repo>
cd Claimguard
git checkout v2-dev
```

### Step 2: Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Download spaCy NLP model (required for field extraction)
python -m spacy download en_core_web_sm

# Frontend
cd ../frontend
npm install
cd ..
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit for production
nano backend/.env  # or use your editor
```

**Required settings:**
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-random-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/claimguard
```

### Step 4: Database Setup

#### Option A: PostgreSQL (Recommended)
```bash
# Create database
createdb claimguard

# Run migrations
cd backend
python db_migration.py --env production
cd ..
```

#### Option B: SQLite (Simpler for MVP)
```bash
# No setup needed, will auto-create
# Tables created on first run
```

### Step 5: Build Frontend

```bash
cd frontend
npm run build
cd ..
```

### Step 6: Start Services

#### Option A: Development Mode
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm start
```

#### Option B: Production Mode
```bash
# Terminal 1 - Backend (using gunicorn)
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Terminal 2 - Frontend (serve build directory)
cd frontend
npm install -g serve
serve -s build -l 3000
```

### Step 7: Verify Installation

```bash
# Test backend API
curl http://localhost:5000/api/health

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@test.com","password":"password123"}'

# Open frontend
# http://localhost:3000
```

---

## Key Features

### 📄 Document Intelligence
- **OCR:** Extract text from images/PDFs using EasyOCR
- **Field Extraction:** Auto-fill form fields using spaCy NER + regex
- **Classification:** Detect document type (claim form, medical report, etc.)
- **Confidence Scores:** Know how confident the AI is about each extraction

### ✅ Smart Validation
- **Data Quality:** Catch invalid dates, unrealistic amounts, vague text
- **Consistency Checks:** Ensure cross-field logic (discharge > admission, etc.)
- **Fraud Detection:** Flag suspicious patterns and calculate risk score
- **Score Adjustment:** Readiness score reflects actual data quality

### 🎨 Human-Friendly UI
- **Status Banner:** Clear status at a glance (green/yellow)
- **Progress Bars:** Visual indicators for completion
- **Grouped Issues:** Organized by type (documents, data, warnings)
- **Plain Language:** No jargon, actionable next steps
- **Mobile Ready:** Works on phones and tablets

---

## Configuration Options

### Environment Variables (backend/.env)

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret

# Database
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/claimguard
# or: sqlite:///backend/instance/claimguard.db

# Storage
STORAGE_TYPE=local           # or 's3'
UPLOAD_FOLDER=/var/claimguard/uploads

# Optional: AWS S3
AWS_STORAGE_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Optional: Email notifications
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Server Configuration

**Nginx (recommended)**
```nginx
upstream claimguard_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name claimguard.example.com;

    location /api/ {
        proxy_pass http://claimguard_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

**Apache**
```apache
<VirtualHost *:80>
    ServerName claimguard.example.com

    ProxyPass /api/ http://127.0.0.1:5000/api/
    ProxyPassReverse /api/ http://127.0.0.1:5000/api/

    ProxyPass / http://127.0.0.1:3000/
    ProxyPassReverse / http://127.0.0.1:3000/
</VirtualHost>
```

---

## Performance Tuning

### Backend Workers
```bash
# Default: 4 workers (good for 10-50 users)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# High traffic (100+ users): Use more workers
gunicorn -w 8 -b 0.0.0.0:5000 app:app

# Calculate: workers = (2 × CPU_count) + 1
```

### Database Optimization
- **PostgreSQL:** Use connection pooling (pgBouncer)
- **SQLite:** Suitable for < 100 concurrent users
- Add indexes on frequently queried fields
- Regular backups (daily recommended)

### OCR Performance
- First document: 5-10 seconds (model loads once)
- Subsequent documents: 2-5 seconds
- Consider async processing for bulk uploads

---

## Monitoring & Logs

### Application Logs
```bash
# Development
tail -f backend/app.log

# Production (systemd)
journalctl -u claimguard-backend -f

# Production (Docker)
docker logs -f claimguard-backend
```

### Health Check
```bash
# Backend health
curl http://localhost:5000/api/health

# Database connection
python -c "from app import db, app; app.app_context().push(); print('DB OK' if db.engine.connect() else 'DB ERROR')"
```

### Database Backup
```bash
# PostgreSQL
pg_dump claimguard > backup-$(date +%Y%m%d).sql

# SQLite
cp backend/instance/claimguard.db backup-$(date +%Y%m%d).db
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'spacy'"
**Solution:**
```bash
python -m spacy download en_core_web_sm
```

### Issue: "OCR not available"
**Solution:**
```bash
pip install easyocr pdf2image
# Also install poppler: apt-get install poppler-utils (Linux)
```

### Issue: "Database connection refused"
**Solution:**
- Check PostgreSQL is running: `psql --version`
- Verify credentials in `.env`
- Check database exists: `psql -l | grep claimguard`

### Issue: "Port 5000 already in use"
**Solution:**
```bash
# Find and kill process using port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
gunicorn -b 0.0.0.0:8000 app:app
```

### Issue: "Frontend shows blank page"
**Solution:**
- Check browser console for errors (F12)
- Verify API endpoint is correct
- Check backend is running: `curl http://localhost:5000/api/health`

---

## Security Checklist

- [ ] Change default test credentials (customer@test.com)
- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Enable HTTPS/SSL certificates
- [ ] Set FLASK_DEBUG=False in production
- [ ] Use strong database passwords
- [ ] Enable database backups
- [ ] Configure firewall (block unused ports)
- [ ] Set up log rotation
- [ ] Regular security updates (`pip list --outdated`)
- [ ] Monitor for suspicious activity

---

## Deployment Platforms

### Heroku
```bash
git push heroku v2-dev:main
```

### AWS EC2
```bash
# Create instance, install dependencies, run:
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### DigitalOcean
```bash
# Create droplet, install dependencies, run:
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker
```bash
# Create Dockerfile (see examples in repo)
docker build -t claimguard:v2 .
docker run -p 5000:5000 claimguard:v2
```

### Kubernetes
```bash
# Create deployment manifests
kubectl apply -f deployment.yaml
```

---

## Support & Documentation

- **Deployment Guide:** `V2_PRODUCTION_DEPLOYMENT.md`
- **Features & Architecture:** `V2_SUMMARY.md`
- **API Documentation:** Backend source code (inline comments)
- **UX Screenshots:** `testing-screenshots/` (if available)

---

## Rollback Procedure

If you need to revert to V1:
```bash
git checkout v1-stable
cd backend && python app.py
```

V1 database and files are untouched. Complete rollback possible.

---

## Next Steps (Phase 5+)

1. **Phase 5:** ML Fraud Detection — Train models on historical data
2. **Phase 6:** Advanced Features — Comparison, deadlines, networks
3. **Phase 7:** Integration — Auto-submit to insurers
4. **Phase 8:** Mobile App — iOS/Android native support
5. **Scaling:** Redis caching, async workers, database replication

---

## Success Indicators

Your deployment is successful when:

- ✅ Backend starts without errors
- ✅ Frontend loads at http://localhost:3000
- ✅ Login works with test credentials
- ✅ Can upload a document
- ✅ OCR extracts text
- ✅ Validation scoring works
- ✅ UI displays validation results in plain language
- ✅ No console errors in browser
- ✅ Database responds to queries

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python app.py` | Start backend (dev) |
| `gunicorn -w 4 -b 0.0.0.0:5000 app:app` | Start backend (prod) |
| `npm start` | Start frontend (dev) |
| `npm run build` | Build frontend (prod) |
| `python -m spacy download en_core_web_sm` | Install NLP model |
| `python db_migration.py` | Migrate database |
| `tail -f backend/app.log` | View logs |
| `curl http://localhost:5000/api/health` | Test backend |

---

## Contact & Support

- **Repository:** [Your Repo URL]
- **Documentation:** This file + phase documentation
- **Issues:** Check `.agents/tasks/` for phase reports

---

**Deployment Date:** October 8, 2026  
**Version:** 2.0.0-MVP  
**Status:** ✅ Production Ready

Good luck with your deployment! 🚀
