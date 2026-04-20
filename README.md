# ClaimGuard

Validate insurance claims before submission. Catch errors early, improve approval rates.

---

## What is ClaimGuard?

ClaimGuard is a full-stack web application that checks your insurance claim for errors **before** you submit it to the insurer. It tells you exactly what documents are missing, what fields are wrong, and gives you a score out of 100.

---

## Current Status

### ✅ Done — Phase 1 (Core Flow)

| Feature | Status |
|---|---|
| Authentication (Register / Login / JWT) | ✅ Done |
| 6 Insurance Types (Health, Vehicle, Life, Property, Travel, Crop) | ✅ Done |
| Document Checklist with file upload | ✅ Done |
| Claim Details Form with live validation | ✅ Done |
| Rule Engine (score out of 100) | ✅ Done |
| Validation Report (score ring, violations, breakdown) | ✅ Done |
| Dashboard (all past claims with scores) | ✅ Done |

### 🚧 Next — Phase 2

| Feature | Status |
|---|---|
| OCR — auto-read uploaded documents | Pending |
| PDF Report Download | Pending |
| Deploy to Vercel + Render + Supabase | Pending |

---

## How to Run

### Backend
```bash
cd backend
pip install -r requirements.txt
python seed_all_types.py    # run once to seed database
python app.py               # starts on http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm start                   # starts on http://localhost:3000
```

---

## Full User Flow

```
Register / Login
      ↓
Home — pick insurance type (6 cards)
      ↓
Documents — checklist + file upload + progress bar
      ↓
Details — dynamic form with live validation
      ↓
Validation — rule engine runs, score calculated
      ↓
Report — score ring, breakdown, violations + fix suggestions
      ↓
Dashboard — all past claims with scores and status
```

---

## Scoring System

| Category | Max Points | How |
|---|---|---|
| Documents | 40 | Weighted by document importance |
| Fields | 35 | Filled fields / total fields × 35 |
| Consistency | 25 | Starts at 25, deducts for violations |
| **Total** | **100** | |

**Labels:**
- 80–100 → Ready to Submit (green)
- 50–79 → Needs Attention (yellow)
- 0–49 → Incomplete (red)

---

## Insurance Types

| Type | Documents | Fields | Consistency Rules |
|---|---|---|---|
| Health | 10 | 8 | 2 |
| Vehicle | 10 | 8 | 1 |
| Life | 9 | 8 | 1 |
| Property | 9 | 8 | 1 |
| Travel | 9 | 8 | 2 |
| Crop | 8 | 8 | 1 |

---

## API Endpoints

### Auth
```
POST /api/auth/register    create account
POST /api/auth/login       sign in
GET  /api/auth/me          get current user
```

### Insurance
```
GET  /api/insurance-types          list all 6 types
GET  /api/rules/:type              documents + fields + rules for type
```

### Claims
```
GET  /api/claims                   list user's claims
POST /api/claims                   create new claim
PUT  /api/claims/:id               update claim data
POST /api/claims/:id/validate      run rule engine
GET  /api/claims/:id/report        get full report
```

### File Upload
```
POST   /api/claims/:id/upload              upload document
GET    /api/claims/:id/documents           list uploaded files
DELETE /api/claims/:id/documents/:docId    delete file
```

---

## Tech Stack

**Backend:** Python Flask · SQLAlchemy · SQLite · Flask-JWT-Extended · bcrypt · Flask-CORS

**Frontend:** React 18 · React Router · Axios · Context API · Custom CSS

**Deploy (planned):** Vercel (frontend) · Render (backend) · Supabase PostgreSQL (database)

---

## Database Tables

| Table | Purpose |
|---|---|
| users | Authentication |
| insurance_types | 6 insurance types |
| rules | Documents, fields, consistency rules |
| claims | User claim attempts |
| violations | Issues found by rule engine |
| claim_documents | Uploaded files |

---

## Color Scheme (Dark Theme)

| Token | Value |
|---|---|
| Background | `#060810` |
| Card | `#0c1120` |
| Border | `#141e35` |
| Primary Blue | `#3b82f6` |
| Cyan | `#06b6d4` |
| Green | `#22c55e` |
| Yellow | `#f59e0b` |
| Red | `#ef4444` |
| Text | `#e2e8f0` |
| Muted | `#475569` |

Fonts: **Syne Bold** (headings) · **DM Sans** (body)
