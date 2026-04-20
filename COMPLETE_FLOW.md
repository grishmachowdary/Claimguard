# ClaimGuard — Complete Application Flow

## ✅ FULLY IMPLEMENTED

### 1. Authentication System
**Register** (`/register`)
- Full name, email, password fields
- Password confirmation validation
- Email uniqueness check
- JWT token generation
- Auto-login after registration

**Login** (`/login`)
- Email + password authentication
- JWT token stored in localStorage
- Error handling for invalid credentials
- Redirects to home after login

**Protected Routes**
- All app pages require authentication
- Auto-redirect to `/login` if not authenticated
- Navbar shows user name and avatar
- Sign out clears token and redirects to login

---

### 2. Home Page (`/`)
**Insurance Type Selection**
- 6 insurance cards displayed:
  - ❤️ Health Insurance
  - 🚗 Vehicle Insurance
  - 🛡️ Life Insurance
  - 🏠 Property Insurance
  - ✈️ Travel Insurance
  - 🌾 Crop Insurance
- Click any card → navigate to Documents page
- "My Claims" button in navbar → Dashboard

---

### 3. Documents Page (`/documents/:insuranceType`)
**Document Checklist**
- Shows all required and optional documents for selected insurance type
- Each document card displays:
  - Document name with Required/Optional badge
  - Suggestion text (what to do)
  - Severity level (high/medium/low)
  - Score weight (points)
  - Checkbox to mark as ready
  - Upload button (PDF, PNG, JPG only, max 16MB)

**File Upload**
- Click "📎 Upload" → file picker opens
- After upload → green checkmark + filename shown
- Remove button (✕) to delete uploaded file
- Auto-checks the document when file uploaded

**Progress Bar**
- Shows X of Y required documents ready
- Percentage display
- Color changes: Red (0-40%) → Yellow (41-79%) → Green (80-100%)

**Missing Documents Warning**
- Red banner shows if required docs missing
- Lists exactly which documents are needed

**Next Button**
- Disabled (grey) until all required documents checked
- Enabled (blue) when all required docs ready
- Click → navigate to Details form

---

### 4. Details Form (`/details/:claimId`)
**Dynamic Form Fields**
- Form fields change based on insurance type selected
- Field types auto-detected:
  - Text fields: names, policy numbers, locations
  - Date fields: admission/discharge, travel dates, sowing/damage dates
  - Number fields: claim amounts, coverage limits
  - Textarea fields: diagnosis, incident description, damage description

**Live Validation**
- Green border + ✓ when field filled correctly
- Red border + error message when invalid
- Real-time checks:
  - Date pairs (discharge after admission, travel end after start, damage after sowing)
  - Amount limits (claim amount vs coverage/sum assured/property value)
  - Required field validation

**Progress Bar**
- Shows X of Y fields filled
- Updates as user types

**Submit Button**
- Disabled if any errors or empty required fields
- Click "Save & Validate Claim" → runs backend validation
- Navigate to Report page

---

### 5. Report Page (`/report/:claimId`)
**Score Display**
- Large circular score ring (0-100)
- Color coded: Green (80+), Yellow (50-79), Red (0-49)
- Readiness label: "Ready to Submit" / "Needs Attention" / "Incomplete"

**Score Breakdown**
- Documents: X/40 points (with progress bar)
- Fields: X/35 points (with progress bar)
- Consistency: X/25 points (with progress bar)

**Uploaded Documents**
- Shows count of uploaded documents
- Green tags for each uploaded document
- Displays document names

**Violations List**
- Sorted by severity: High → Medium → Low
- Each violation shows:
  - Severity badge (color coded)
  - Error message (what's wrong)
  - Fix suggestion (💡 how to fix it)
- "All Clear ✓" message if no violations

**Claim Summary**
- Shows all form data entered
- Key-value pairs for easy review

**Action Buttons**
- "View All Claims" → Dashboard
- "Edit Details" → back to form
- "Start New Claim" → Home

---

### 6. Dashboard (`/dashboard`)
**My Claims List**
- Shows all claims created by logged-in user
- Each claim card displays:
  - Claim ID number
  - Insurance type name
  - Primary field (policy number or vehicle number)
  - Score (color coded)
  - Readiness label badge
  - Created date

**Empty State**
- Shows when no claims exist
- "Start New Claim" button

**Click any claim** → view full report

---

## Backend Features

### Database Tables
1. **users** — authentication
2. **insurance_types** — 6 types
3. **rules** — documents, fields, consistency rules for each type
4. **claims** — user claims with form data
5. **violations** — validation issues
6. **claim_documents** — uploaded files

### API Endpoints
**Auth**
- POST `/api/auth/register` — create account
- POST `/api/auth/login` — sign in
- GET `/api/auth/me` — get current user (JWT protected)

**Insurance**
- GET `/api/insurance-types` — list all 6 types
- GET `/api/rules/:type` — get documents/fields/rules for type

**Claims**
- GET `/api/claims` — list user's claims
- POST `/api/claims` — create new claim
- PUT `/api/claims/:id` — update claim data
- POST `/api/claims/:id/validate` — run validation engine
- GET `/api/claims/:id/report` — get full report

**File Upload**
- POST `/api/claims/:id/upload` — upload document
- GET `/api/claims/:id/documents` — list uploaded files
- DELETE `/api/claims/:id/documents/:docId` — delete file

### Rule Engine
**Document Score (40 points)**
- Each required document has a weight
- Sum of weights for uploaded docs / total required weights × 40

**Field Score (35 points)**
- Filled fields / total fields × 35

**Consistency Score (25 points)**
- Starts at 25
- Deducts points for violations:
  - High severity: -15 points
  - Medium severity: -10 points
  - Low severity: -5 points

**Final Score** = Document + Field + Consistency (0-100)

---

## Technology Stack

**Backend**
- Flask (Python web framework)
- SQLAlchemy (ORM)
- SQLite (database)
- Flask-JWT-Extended (authentication)
- bcrypt (password hashing)
- Flask-CORS (cross-origin requests)

**Frontend**
- React 18
- React Router (navigation)
- Axios (API calls)
- Context API (auth state)
- Custom CSS (dark theme)

**File Storage**
- Local filesystem: `backend/uploads/:claim_id/`
- Organized by claim ID

---

## Color Scheme (Dark Theme)
- Background: `#060810`
- Card surface: `#0c1120`
- Border: `#141e35`
- Primary blue: `#3b82f6`
- Cyan: `#06b6d4`
- Green: `#22c55e`
- Yellow: `#f59e0b`
- Red: `#ef4444`
- Text: `#e2e8f0`
- Muted text: `#475569`

---

## How to Run

**Backend**
```bash
cd backend
pip install -r requirements.txt
python seed_all_types.py  # First time only
python app.py
```
Runs on http://localhost:5000

**Frontend**
```bash
cd frontend
npm install
npm start
```
Runs on http://localhost:3000

---

## Test the Complete Flow

1. Open http://localhost:3000
2. Click "Create one" → Register with name, email, password
3. Auto-logged in → see Home page with 6 insurance cards
4. Click "Health Insurance"
5. See 10 documents (8 required, 2 optional)
6. Check all 8 required documents
7. Upload at least one PDF file
8. Progress bar turns green → Next button activates
9. Click "Next: Fill Claim Details"
10. Fill all 8 fields (patient name, dates, amounts, etc.)
11. Watch live validation (green borders, error messages)
12. Click "Save & Validate Claim"
13. See report with score, breakdown, violations
14. Click "View All Claims" → Dashboard
15. See your claim listed with score
16. Click claim → view report again
17. Click "Start New Claim" → repeat for other insurance types

---

## All 6 Insurance Types Working

Each type has its own:
- Document requirements (8-10 documents)
- Form fields (8 fields)
- Consistency rules (1-2 rules)
- Validation logic

Test with Vehicle, Life, Property, Travel, and Crop insurance to see different documents and fields!

---

## Status: ✅ PRODUCTION READY

All features implemented and tested. Ready for deployment.
