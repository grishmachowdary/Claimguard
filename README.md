# ClaimGuard

Validate insurance claims before submission. Catch errors early, improve approval rates.

---

## What is ClaimGuard?

ClaimGuard is a full-stack web application that checks your insurance claim for errors **before** you submit it to the insurer. It tells you exactly what documents are missing, what fields are wrong, gives you a score out of 100, and predicts your approval probability using AI.

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

## User Roles

| Role | Access |
|---|---|
| **Customer** | File claims, upload documents, view reports |
| **Agent** | Manage client portfolio, view all client claims |
| **Insurer** | Review submitted claims, approve or reject |

Register at `/register` and select your role.

---

## Complete Feature List

### Authentication
- Register / Login with JWT
- 3 roles: Customer, Agent, Insurer
- Auto-redirect to correct portal after login
- JWT stored in localStorage, auto-attached to all requests
- Global 401 handler — auto-redirect to login on token expiry

### Insurance Types (6)
Health · Vehicle · Life · Property · Travel · Crop

Each type has its own documents, form fields, and validation rules.

### Document Checklist
- Required and optional documents per insurance type
- File upload (PDF, PNG, JPG — max 16MB)
- Progress bar (red → yellow → green)
- Missing documents warning with exact list
- Next button disabled until all required docs uploaded

### Claim Details Form
- Dynamic fields based on insurance type
- Live validation as you type
- Date pair checks (admission before discharge, travel start before end)
- Amount vs coverage checks
- Auto-save draft to localStorage — restored if you close browser
- Step progress indicator (Select → Documents → Details → Report)

### Validation Engine (Score out of 100)
| Category | Max Points | How |
|---|---|---|
| Documents | 40 | Weighted by document importance |
| Fields | 35 | Filled fields / total × 35 |
| Consistency | 25 | Starts at 25, deducts for violations |

**Labels:** Ready to Submit (80+) · Needs Attention (50–79) · Incomplete (0–49)

### Validation Report
- Score ring with percentage
- Score meter bar (Incomplete → Needs Attention → Ready)
- Breakdown bars: Documents / Fields / Consistency with exact counts
- Document status table (green = uploaded, red = missing)
- Field completion grid
- Violations list sorted by severity (High → Medium → Low)
- "Fix Now" button on violations — goes back to form

### AI Claim Report
- Approval probability percentage (0–100%)
- Circular approval ring (green/yellow/red)
- Summary paragraph explaining claim status
- Score deductions table (what reduced the percentage)
- Issues list with severity dots
- How to Improve suggestions

### Claim Status Tracker
Timeline with 8 steps:
📋 Created → 📎 Documents → ✏️ Details → ✅ Ready → 🚀 Submitted → 🔍 Under Review → 🎉 Approved / ❌ Rejected

- Pulsing blue ring on current step
- Timestamps for each completed step
- "Next steps" guidance box

### Submission Deadline Tracker
- Countdown to submission deadline
- Health/Vehicle/Property/Travel: 30 days from incident
- Life: 90 days from date of death
- Crop: 72 hours from damage
- Color changes: Green → Yellow (7 days) → Red (3 days) → EXPIRED

### Claim History Comparison
- Compares current claim with previous claims of same type
- Score diff: Previous 45 → This claim 82 (+37 pts)
- Lists what improved and what got worse

### Rejection Risk Predictor
- Predicts rejection probability (0–95%)
- Detects pre-existing conditions in diagnosis
- Flags missing FIR for vehicle claims
- Warns when claim amount is near coverage limit
- High / Moderate / Low risk levels

### Approved Network
- Insurance-approved hospitals, garages, contractors per type
- Shows cashless availability, speciality, supported insurers, star rating
- Message changes based on claim risk level

### Smart Document Analyzer
- Extracts text from uploaded PDFs
- Name consistency check (fuzzy matching)
- Policy number verification
- Date range validation
- Amount mismatch detection

### QR Code
- Each claim gets a unique QR code
- Scan to open claim report directly in browser
- Download QR as PNG image
- Copy claim URL to clipboard

### Submit to Insurer
- 8 partner insurance companies
- Filtered by insurance type
- Score check before submission (min 50 to submit)
- Reference number generated on submission
- Claim status updated to "Submitted"

### Claim-Ready Package (PDF Download)
- Professional PDF with all claim details
- AI summary, validation score, document checklist
- Violations with fix suggestions
- ClaimGuard branding

### Agent Dashboard (`/agent`)
- Stats: total clients, avg score, ready/submitted/approved
- Add clients by email
- View all client claims with scores and status
- Remove clients from portfolio

### Insurer Portal (`/insurer`)
- Stats: total received, pending, approved, rejected, approval rate
- Filter claims by status (New / Under Review / Approved / Rejected)
- Review panel: claimant info, validation score, full report link
- Actions: Mark Under Review / Request Info / Approve / Reject
- Notes field for each action
- Pagination (15 per page)

### Multi-language Support
English 🇬🇧 · हिंदी 🇮🇳 · தமிழ் 🇮🇳 · मराठी 🇮🇳

Language selector in navbar, persists in localStorage.

### Dashboard
- All past claims with scores and status
- Color-coded status dots (blinking for active states)
- Pagination (10 per page)
- Stats: Total / Ready / Needs Attention / Incomplete

---

## API Endpoints

### Auth
```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Insurance
```
GET  /api/insurance-types
GET  /api/rules/:type
GET  /api/network/:type
```

### Claims
```
GET  /api/claims
POST /api/claims
PUT  /api/claims/:id
POST /api/claims/:id/validate
GET  /api/claims/:id/report
GET  /api/claims/:id/status
PUT  /api/claims/:id/status
GET  /api/claims/:id/deadline
GET  /api/claims/:id/comparison
GET  /api/claims/:id/qr
POST /api/claims/:id/submit
POST /api/claims/:id/analyze
GET  /api/claims/:id/package
```

### File Upload
```
POST   /api/claims/:id/upload
GET    /api/claims/:id/documents
DELETE /api/claims/:id/documents/:docId
```

### Agent
```
GET    /api/agent/stats
GET    /api/agent/clients
POST   /api/agent/clients
DELETE /api/agent/clients/:id
GET    /api/agent/clients/:id/claims
```

### Insurer
```
GET /api/insurer/stats
GET /api/insurer/claims
PUT /api/insurer/claims/:id/review
```

---

## Database Tables

| Table | Purpose |
|---|---|
| users | Authentication + roles |
| insurance_types | 6 insurance types |
| rules | Documents, fields, consistency rules |
| claims | User claim attempts |
| violations | Issues found by rule engine |
| claim_documents | Uploaded files |
| claim_status_history | Status change log |
| agent_clients | Agent ↔ client relationships |

---

## Tech Stack

**Backend:** Python Flask · SQLAlchemy · SQLite · Flask-JWT-Extended · bcrypt · Flask-CORS · ReportLab · fuzzywuzzy · qrcode

**Frontend:** React 18 · React Router · Axios · Context API · Custom CSS

**Deploy (planned):** Vercel (frontend) · Render (backend) · Supabase PostgreSQL (database)

---

## Color Scheme

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
