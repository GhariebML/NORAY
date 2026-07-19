# /import_linkedin — Import LinkedIn Profile Export

You are importing a LinkedIn profile export (PDF) into the NORAY career profile system.

The user provides a file path as `$ARGUMENTS`.

---

## Step 0: Resolve File Path

If `$ARGUMENTS` is empty, ask the user for the LinkedIn export file.

If `$ARGUMENTS` is a relative filename, check `documents/linkedin/` first.

Supported format: `.pdf` (LinkedIn "Save to PDF" export)

Verify the file exists. If not, tell the user and stop.

---

## Step 1: Parse LinkedIn Export

Read the PDF and extract text content.

LinkedIn PDF exports follow a predictable structure:
- Name (first line, large text)
- Headline
- Location
- About/Summary
- Experience (title, company, dates)
- Education (institution, degree, dates)
- Skills (with endorsement counts)
- Certifications
- Languages

---

## Step 2: Load Existing Profile

Read `career_profile.json` if it exists.

LinkedIn data is a **cross-reference source** — it fills gaps but doesn't overwrite CV-sourced data. The CV is considered more authoritative for dates and titles.

---

## Step 3: Extract and Compare

Extract structured sections from the LinkedIn export.

For each section, compare against the existing profile:

**LinkedIn fills gaps when:**
- A job exists in LinkedIn but not in the CV (add it)
- A skill is endorsed on LinkedIn but not in the CV (add to skills)
- A certification is listed on LinkedIn but not in the CV (add it)
- The About section provides behavioral signals not yet captured

**LinkedIn does NOT overwrite:**
- Job titles (CV is more authoritative)
- Dates (CV is more authoritative)
- Education details (CV is more authoritative)

---

## Step 4: Present Changes

```
## LinkedIn Import — Changes Detected

### New Experience (from LinkedIn, not in CV)
- [ ] Teaching Assistant at University of Copenhagen (2020-2021)
  - Assisted with Machine Learning course

### New Skills (endorsed on LinkedIn)
- [ ] Python (15 endorsements)
- [ ] Machine Learning (12 endorsements)
- [ ] Data Analysis (8 endorsements)

### New Certification
- [ ] AWS Certified Solutions Architect — Amazon (2023)

### Behavioral Signal (from About section)
- [ ] Work style: "I thrive in collaborative, fast-paced environments..."

### Already Present (no changes)
- 3 experience entries ✓
- 5 education entries ✓
```

Wait for user confirmation before applying.

---

## Step 5: Apply and Sync

After confirmation:
1. Backup existing profile
2. Merge LinkedIn data (gaps only, no overwrites)
3. Save `career_profile.json`
4. Sync legacy skill files

---

## Step 6: Report Results

```
## ✅ LinkedIn Import Complete

**Source:** linkedin_profile.pdf
**New data added:**
- 1 experience entry (gap fill)
- 6 skills (from endorsements)
- 1 certification
- Behavioral profile update

**Note:** LinkedIn data was used to fill gaps only. CV-sourced data was preserved.

Run `/import_github` to also add your GitHub projects.
```

---

## Important Rules

1. **LinkedIn is a cross-reference, not a primary source.** CV data takes precedence for dates and titles.
2. **Skills from endorsements are useful but noisy.** Add them but note they're endorsement-based.
3. **The About section is rich behavioral signal.** Extract work style, values, and communication patterns.
4. **Never overwrite CV-sourced data without asking.**
