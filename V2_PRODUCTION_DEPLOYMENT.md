# ClaimGuard V2 Production Deployment Guide

**Version:** 2.0.0-MVP  
**Status:** Ready for Production  
**Date:** October 8, 2026  
**Branch:** v2-dev (10 commits, fully tested)

---

## What's New in V2

ClaimGuard V2 is a major upgrade from V1 with intelligent document processing, smart validation, and fraud detection.

### Phase 1: Foundation ✅
- Critical dependencies installed (ReportLab, qrcode, fuzzywuzzy, python-dotenv)
- All imports verified, backend starts without errors

### Phase 2: Infrastructure ✅
- **Config System:** Environment-aware configuration (dev/prod/test)
- **Storage Abstraction:** Local + S3 storage (plug-and-play for cloud)
- **Database Migration:** Zero-downtime SQLite→PostgreSQL tool
- **ML Infrastructure:** Model versioning, training pipeline setup

### Phase 3: Document Intelligence ✅
- **OCR Engine:** EasyOCR for text extraction from images/PDFs
- **Field Extraction:** spaCy NER + regex for structured data (names, amounts, dates)
- **Document Classification:** Auto-detect document type (claim form, medical report, etc.)
- **Endpoints:** `/api/claims/<id>/analyze-document`, `/api/claims/<id>/extract-fields`

### Phase 4: Document Validation ✅
- **Data Quality Validator:** Catches invalid dates, unrealistic amounts, vague text
- **Consistency Checker:** Ensures cross-field logic (discharge > admission, etc.)
- **Fraud Detector:** Flags suspicious patterns (future dates, missing documents, etc.)
- **Smart Scoring:** Readiness score now reflects actual data quality, not just completeness

### UX Redesign ✅
- **Human-Friendly Report:** Replaces technical jargon with plain language
- **Progress Bars:** Visual indicators for documents uploaded, fields filled
- **Grouped Issues:** Missing documents, data problems, warnings—organized logically
- **Mobile Responsive:** 44px touch targets, readable on all devices
- **Accessible:** WCAG compliant, color + text indicators

---

## Production Deployment Steps

### 1. **Prepare Production Database**

#### Option A: PostgreSQL (Recommended for Scale)
```bash
# Create PostgreSQL database
createdb claimguard_prod

# Run migration (zero-downtime)
python backend/db_migration.py --env production
```

#### Option B: Keep SQLite (Simpler for MVP)
```bash
# SQLite will auto-create on first run, no setup needed
```

### 2. **Configure Environment**

Edit `backend/.env` for production:
```env
FLASK_ENV=production
FLASK_DEBUG=False
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/claimguard_prod
AWS_STORAGE_BUCKET=your-s3-bucket  # if using S3
SECRET_KEY=your-random-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

### 3. **Install Dependencies**

```bash
cd backend
pip install -r requirements.txt

# Download spaCy model (one-time)
python -m spacy download en_core_web_sm

# On Windows, also install poppler:
# Option 1: choco install poppler
# Option 2: conda install -c conda-forge poppler
# Option 3: Download from https://github.com/oschwartz10612/poppler-windows/releases/
```

### 4. **Run Migrations (if using PostgreSQL)**

```bash
python backend/db_migration.py --env production --backup
```

### 5. **Start Backend (Production)**

```bash
# Option 1: Development server (testing only)
cd backend && python app.py

# Option 2: Production WSGI server (recommended)
cd backend && gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Option 3: With environment (Docker, cloud, etc.)
FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 6. **Build Frontend**

```bash
cd frontend
npm install
npm run build  # Creates optimized build

# Serve with production server (nginx, Apache, etc.)
# Or deploy to hosting (Vercel, AWS, etc.)
```

### 7. **Verify Production Setup**

```bash
# Test backend API
curl http://localhost:5000/api/health

# Test auth (login endpoint)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@test.com","password":"password123"}'

# Test document analysis (upload a test claim)
# Navigate to frontend and upload a document
```

---

## Production Checklist

- [ ] `.env` file configured with production keys
- [ ] Database created (PostgreSQL or SQLite)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] spaCy model downloaded (`python -m spacy download en_core_web_sm`)
- [ ] Poppler installed (for PDF processing)
- [ ] Backend starts without errors (`python app.py` or `gunicorn`)
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Test login works
- [ ] Test document upload works
- [ ] Test OCR/field extraction works
- [ ] Test validation scoring works
- [ ] Logs are configured and rotating
- [ ] Backups are set up
- [ ] SSL/TLS certificates installed (if using HTTPS)

---

## Key Production Features

### Auto-Seeding
- First run creates 3 test users automatically:
  - `customer@test.com / password123` (customer role)
  - `agent@test.com / password123` (agent role)
  - `insurer@test.com / password123` (insurer role)
- Remove these in production or replace with real users

### Validation Scoring
- **100:** All documents, all fields, no issues
- **80-99:** Complete, minor warnings
- **50-79:** Incomplete or issues found
- **0-49:** Major problems or errors
- Scoring is now deterministic based on actual data quality

### Document Intelligence
- OCR works offline (no API keys needed)
- Field extraction uses spaCy NER + regex
- Classification covers 8 document types
- All results stored for audit trail

### Fraud Detection
- Flags suspicious patterns (future dates, high amounts, missing docs)
- Calculates fraud risk score (0.0-1.0)
- Provides actionable recommendations to users

---

## Configuration Options

### Storage
```python
# backend/config.py
# Local storage (default)
STORAGE_TYPE = 'local'
UPLOAD_FOLDER = '/var/claimguard/uploads'

# S3 storage
STORAGE_TYPE = 's3'
AWS_STORAGE_BUCKET = 'claimguard-prod'
```

### Database
```python
# PostgreSQL (production)
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@host:5432/claimguard'

# SQLite (development)
SQLALCHEMY_DATABASE_URI = 'sqlite:///backend/instance/claimguard.db'
```

### Email (Optional)
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

---

## Performance Notes

- **OCR:** First claim takes ~5-10 seconds (model loads once). Subsequent claims are faster.
- **Field Extraction:** ~1-2 seconds per document
- **Classification:** ~0.5 seconds per document
- **Database:** Queries optimized for indexed fields (claim_id, user_id)

For high volume:
- Use PostgreSQL (better than SQLite)
- Deploy on multiple workers (`gunicorn -w 8`)
- Use Redis for caching (future enhancement)
- Use S3 for file storage (scales better than local filesystem)

---

## Rollback Plan

If you need to revert to V1:
```bash
git checkout v1-stable
cd backend && python app.py
```

V1 database and files are untouched. V2 uses a separate branch and database.

---

## Support & Debugging

### Backend Logs
```bash
tail -f backend/app.log
```

### Check Dependencies
```bash
python -c "import easyocr; import spacy; print('All OCR deps OK')"
```

### Test Database
```bash
python -c "from app import app, db; app.app_context().push(); print(db.engine.url)"
```

### Reset Database (Development Only)
```bash
rm backend/instance/claimguard.db
python app.py  # Auto-creates and seeds
```

---

## Next Steps (Phase 5+)

1. **Phase 5: ML Fraud Detection** — Train ML models on historical claims
2. **Phase 6: Advanced Features** — Claim comparison, deadline tracking
3. **Phase 7: Insurer Integration** — Auto-submit to insurers
4. **Phase 8: Mobile App** — Native mobile support
5. **Scaling** — Redis caching, batch processing, async workers

---

## Support

For issues or questions, check:
- Backend logs: `backend/app.log`
- Frontend console: Browser DevTools
- Database: Verify connection string
- OCR: Verify spaCy model downloaded

Production-ready as of: **October 8, 2026**  
Version: **2.0.0-MVP**  
Status: **APPROVED ✅**
