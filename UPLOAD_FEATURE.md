# File Upload Feature

## Overview
Users can now upload documents directly to their claims. Files are stored on the backend and linked to specific document types.

## Features Implemented

### Backend
- **File Upload Endpoint**: `POST /api/claims/:id/upload`
  - Accepts PDF, PNG, JPG, JPEG files
  - Max file size: 16MB
  - Files stored in `backend/uploads/:claim_id/` folder
  - Unique filenames with timestamps

- **Get Documents**: `GET /api/claims/:id/documents`
  - Returns all uploaded files for a claim

- **Delete Document**: `DELETE /api/claims/:id/documents/:doc_id`
  - Removes file from filesystem and database

- **New Database Table**: `claim_documents`
  - Tracks uploaded files with metadata
  - Links files to claims and document types

### Frontend
- **FileUpload Component**: Upload button with validation
  - File type validation (PDF, PNG, JPG only)
  - File size validation (16MB max)
  - Upload progress indication
  - Error handling

- **UploadedFiles Component**: Display uploaded files
  - Shows file name and size
  - Delete functionality
  - Auto-updates document checklist

- **Documents Page Integration**:
  - Upload button for each document type
  - Shows uploaded files below each document
  - Auto-marks documents as complete when files uploaded
  - Progress bar updates automatically

## How It Works

1. User selects insurance type
2. Claim is created immediately
3. User uploads files for each document type
4. Files are saved with document type association
5. Document checklist auto-updates
6. User proceeds to fill form details
7. Validation includes uploaded documents

## File Storage Structure
```
backend/uploads/
  ├── 1/  (claim_id)
  │   ├── insurance_policy_card_20260312_143022_policy.pdf
  │   ├── patient_photo_id_20260312_143045_aadhaar.jpg
  │   └── ...
  ├── 2/
  └── ...
```

## Security
- File type validation on both frontend and backend
- File size limits enforced
- Secure filename generation
- Files isolated per claim

## Next Steps
- Add file preview (PDF viewer, image preview)
- OCR text extraction from uploaded documents
- Auto-fill form fields from extracted data
- Compress images before upload
- Add drag-and-drop upload
