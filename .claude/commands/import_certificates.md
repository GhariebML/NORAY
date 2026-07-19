# /import_certificates — Import Certificates and Diplomas

You are importing certificates, diplomas, and transcripts into the NORAY career profile system.

---

## Step 0: Determine Source

If `$ARGUMENTS` contains a file path, import that specific file.

If `$ARGUMENTS` is empty, scan `documents/diplomas/` for all certificate files.

Supported formats: `.pdf`, `.png`, `.jpg`, `.jpeg`

---

## Step 1: Scan and Inventory

List all files found:

```
## Certificates Found in documents/diplomas/

1. MSc_Diploma.pdf — University of Copenhagen
2. AWS_Certified.pdf — Amazon Web Services
3. Coursera_ML_Certificate.pdf — Coursera / Stanford
```

If the folder is empty or only contains `.gitkeep`, tell the user to add certificate files first.

---

## Step 2: Parse Each Certificate

For each certificate file:

**PDF certificates:**
Extract text content. Look for:
- Certificate type (diploma, course certificate, professional cert)
- Recipient name
- Issuer (university, organization, platform)
- Date issued/completed
- Credential ID (if present)
- Hours/credits (if present)
- Credential URL (if present)

**Image certificates:**
If OCR is available (pytesseract), extract text via OCR.
If OCR is not available, ask the user to describe the certificate.

---

## Step 3: Classify and Extract

For each certificate, determine:

**Is it a degree/diploma?**
→ Add to `education` in the profile
- Degree level (BSc, MSc, PhD, Diploma)
- Field of study
- Institution
- Graduation year

**Is it a course/professional certificate?**
→ Add to `certifications` in the profile
- Certificate name
- Issuer
- Date
- Hours (if mentioned)
- Credential URL (if present)

---

## Step 4: Present Changes

```
## Certificate Import — Changes Detected

### Education (Diplomas)
- [ ] MSc in Computer Science — University of Copenhagen (2022)

### Certifications
- [ ] AWS Certified Solutions Architect — Amazon Web Services (2023)
  - Credential ID: ABC123XYZ
- [ ] Machine Learning Specialization — Coursera/Stanford (2021)
  - 120 hours

### Already Present
- BSc in Computer Science ✓
```

Wait for user confirmation.

---

## Step 5: Apply and Sync

After confirmation:
1. Backup existing profile
2. Add confirmed entries to profile
3. Save `career_profile.json`
4. Sync legacy skill files

---

## Step 6: Report Results

```
## ✅ Certificate Import Complete

**Files processed:** 3
**New data added:**
- 1 education entry (MSc diploma)
- 2 certifications

**Files updated:**
- career_profile.json
- 01-candidate-profile.md
```

---

## Important Rules

1. **Distinguish diplomas from certificates.** Diplomas go to education, certificates go to certifications.
2. **Extract credential IDs when present.** Useful for verification.
3. **OCR is best-effort.** If confidence is low, show the raw OCR text and ask the user to verify.
4. **Never fabricate data.** Only extract what's actually in the certificate.
