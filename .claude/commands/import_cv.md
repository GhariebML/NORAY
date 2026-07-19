# /import_cv — Import CV/Resume into Career Profile

You are importing a CV/resume file into the NORAY career profile system.

The user provides a file path as `$ARGUMENTS`. This can be:
- A direct file path: `/import_cv D:\documents\my_cv.pdf`
- A filename in `documents/cv/`: `/import_cv my_cv.pdf`

---

## Step 0: Resolve File Path

If `$ARGUMENTS` is empty, ask the user which CV file to import.

If `$ARGUMENTS` is a relative filename, check `documents/cv/` first, then the project root.

If `$ARGUMENTS` is an absolute path, use it directly.

Supported formats: `.pdf`, `.tex`, `.docx`

Verify the file exists. If not, tell the user and stop.

---

## Step 1: Parse the CV

Read the CV file using the appropriate method:

**PDF files:**
Read the file and extract all text content.

**LaTeX files:**
Read the `.tex` file directly. Strip LaTeX commands but preserve structure.

**DOCX files:**
Read the `.docx` file and extract paragraph text.

---

## Step 2: Load Existing Profile

Read `career_profile.json` if it exists. If it doesn't exist, start with an empty profile structure.

Also read `01-candidate-profile.md` for cross-reference.

---

## Step 3: Extract Structured Data

From the CV text, extract:

1. **Identity**: Name, email, phone, location, LinkedIn URL, GitHub URL
2. **Education**: Degree, field, institution, dates, thesis
3. **Experience**: Title, company, location, dates, responsibilities, achievements
4. **Skills**: Primary, secondary, domain, tools/software
5. **Certifications**: Name, issuer, date
6. **Publications**: Authors, title, journal, year
7. **Awards**: Name, event, year

For each field, check if it's a placeholder token (contains `[` brackets) — skip those.

---

## Step 4: Compute Diff

Compare extracted data against the existing profile:

**New items** (not in existing profile):
- List what will be added

**Conflicting items** (different values for the same field):
- Show both versions and ask the user which to keep

**Skip items** (already in profile):
- Note what's already there and won't be changed

Present the diff to the user:

```
## CV Import — Changes Detected

### New Education
- [ ] MSc in Data Science, University of Copenhagen (2020-2022)

### New Experience
- [ ] Data Scientist at Novo Nordisk (2022-present)
  - Built ML pipelines for drug discovery
  - Reduced analysis time by 40%

### New Skills
- [ ] Primary: PyTorch, TensorFlow, scikit-learn
- [ ] Tools: MLflow, Airflow, dbt

### Conflicts
1. **Email:**
   Existing: old@email.com
   CV: new@email.com
   Which to keep? [keep_existing] [use_cv] [skip]

### Already Present (no changes)
- Name: [Your Name] ✓
- BSc in Computer Science ✓
```

---

## Step 5: Apply Changes

After the user confirms:

1. Backup existing `career_profile.json` (if it exists)
2. Apply confirmed changes to the profile
3. Save `career_profile.json`
4. Update legacy skill files (01-candidate-profile.md) for backward compatibility
5. Update `CLAUDE.md` if identity fields changed

---

## Step 6: Report Results

```
## ✅ CV Import Complete

**Source:** my_cv.pdf
**New data added:**
- 2 education entries
- 3 experience entries
- 8 skills
- 1 certification

**Files updated:**
- career_profile.json
- 01-candidate-profile.md
- CLAUDE.md (identity section)

Run `/setup` to fill in additional profile sections (behavioral, goals, search config).
```

---

## Important Rules

1. **Never overwrite without asking.** Always show conflicts and let the user decide.
2. **Never fabricate data.** Only extract what's actually in the CV.
3. **Backup before writing.** Create a timestamped backup of the existing profile.
4. **Pattern matching is best-effort.** Complex CVs may need manual review. Tell the user if extraction confidence is low.
5. **Sync legacy files.** Always update the skill files so existing Claude Code commands work.
