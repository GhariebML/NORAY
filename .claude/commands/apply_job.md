# /apply_job — Generate Job Application (CV + Cover Letter)

You are generating a complete job application: ATS-optimized CV and targeted cover letter.

`$ARGUMENTS` can be:
- A URL to a job posting
- Pasted job description text
- A company name and role (to search for the posting)

---

## Step 0: Parse Input

If `$ARGUMENTS` looks like a URL, use `WebFetch` to retrieve the job posting.
If it's pasted text, use it directly.
If it's a company name + role, search for the posting via WebSearch.

Extract: **company name**, **role title**, **location**, **language** (Danish or English), and the full job description text.

---

## Step 1: Load Profile

Read `career_profile.json` for the candidate's full profile.
Also read `03-writing-style.md` for writing style rules.
Also read `05-cv-templates.md` for CV template structure.
Also read `06-cover-letter-templates.md` for cover letter template structure.

---

## Step 2: Evaluate Fit

Using the profile and the job posting:

1. **Skills Match (0-100):** Required/preferred skills vs candidate's skills
2. **Experience Match (0-100):** Work history relevance to the role
3. **Education Match (0-100):** Degree level and field alignment
4. **Location Fit (pass/fail):** Geographic compatibility
5. **Overall Fit Score:** Weighted average

Present the evaluation:

```
## Job Fit Evaluation

| Dimension | Score | Notes |
|-----------|-------|-------|
| Skills Match | 85/100 | Strong match on Python, ML, scikit-learn. Gap in Kubernetes. |
| Experience Match | 90/100 | Data science experience at Google maps directly. |
| Education Match | 80/100 | BSc in CS is relevant, MSc would strengthen. |
| Location | ✅ Pass | Copenhagen-based, within range. |
| **Overall** | **85/100** | **Strong fit — recommend proceeding** |

### Key Strengths
- Python + ML expertise matches core requirements
- Previous data science experience in similar industry

### Gaps to Address
- Kubernetes (mention Docker experience as bridge)
- No direct experience with their specific domain (reframe adjacent experience)
```

Ask: "Should I proceed with drafting the CV and cover letter?"

---

## Step 3: Draft CV

Read `cv/main_example.tex` as the template reference.

Generate a tailored CV at `cv/main_{company}.tex`:

1. **Profile statement** — tailored to this specific role and company
2. **Core Competencies** — reordered to match job requirements
3. **Professional Experience** — bullets reordered by relevance, keywords from posting used naturally
4. **Education** — standard
5. **Projects** — most relevant projects included
6. **Certifications/Awards** — if relevant

**Key rules:**
- Use moderncv/banking style
- Keep to exactly 2 pages
- Use `\needspace{5\baselineskip}` before `\cventry` to prevent orphaned titles
- Use keywords from the posting naturally for ATS optimization
- Never fabricate skills or experience

---

## Step 4: Draft Cover Letter

Generate a targeted cover letter at `cover_letters/cover_{company}_{role}.tex`:

1. **Opening** — specific connection to the company/role
2. **Motivation** — why this role and company
3. **Evidence** — 2-3 most relevant achievements
4. **Closing** — forward-looking, confident

**Key rules:**
- Match the language of the job posting (Danish → Danish, English → English)
- Use cover.cls template with Lato/Raleway fonts
- Keep to exactly 1 page
- Follow `03-writing-style.md` rules (no em-dashes, no cliches)
- Address to a named person if available, otherwise "Dear Hiring Manager"
- Any mention of AI tooling must reference **Claude Code** by name

---

## Step 5: Compile & Inspect PDFs (MANDATORY)

Never skip this step.

### Compile CV
```bash
cd cv && lualatex -interaction=nonstopmode main_{company}.tex
```

### Compile Cover Letter
```bash
cd cover_letters && xelatex -interaction=nonstopmode cover_{company}_{role}.tex
```

### Inspect CV (must pass all)
- [ ] Exactly 2 pages
- [ ] No orphaned `\cventry` titles at page bottom
- [ ] No awkward whitespace gaps
- [ ] Section headings not isolated at top of page 2

### Inspect Cover Letter (must pass all)
- [ ] Exactly 1 page
- [ ] Signature block visible, not cut off
- [ ] Bullet font matches body text

### Iterate until clean
If any check fails, edit the .tex file and recompile. Common fixes:
- `\needspace{5\baselineskip}` before problematic `\cventry`
- `\enlargethispage{2-3\baselineskip}` for trailing sections
- Relevance-weighted content cutting for overflow

### Cleanup
Delete `.aux`, `.log`, `.out` files after clean compile.

---

## Step 6: Verification Checklist

Run the full verification checklist before presenting:

### Factual accuracy
- [ ] All claims match actual profile data
- [ ] Job titles, dates, company names correct
- [ ] Contact details correct
- [ ] Company-specific claims verified via WebFetch/WebSearch

### Targeting
- [ ] Profile statement tailored to this role
- [ ] Skills/experience reframed to match requirements
- [ ] Key job requirements addressed
- [ ] Nice-to-have requirements highlighted where matching

### Consistency
- [ ] CV follows moderncv/banking format (2 pages)
- [ ] Cover letter uses cover.cls (1 page)
- [ ] Tone consistent across both documents
- [ ] No contradictions between CV and cover letter

### Quality
- [ ] No LaTeX syntax errors
- [ ] No spelling/grammar errors
- [ ] AI tooling references mention Claude Code by name

---

## Step 7: Present Final Output

```
## ✅ Application Ready

**Role:** Data Scientist at Novo Nordisk
**Fit Score:** 85/100 (Strong fit)

### Files Created
- `cv/main_novo_nordisk.tex` → `cv/main_novo_nordisk.pdf` (2 pages ✅)
- `cover_letters/cover_novo_nordisk_data_scientist.tex` → `cover_letters/cover_novo_nordisk_data_scientist.pdf` (1 page ✅)

### Key Tailoring Decisions
1. Emphasized Python + ML experience (matches core requirements)
2. Referenced healthcare domain experience as bridge to pharma
3. Highlighted stakeholder communication skills (mentioned in posting)
4. Addressed Kubernetes gap by pivoting to Docker experience

### Verification Checklist
- ✅ Factual accuracy — all claims match profile
- ✅ Targeting — profile statement and bullets tailored
- ✅ Consistency — tone and content aligned
- ✅ Quality — compiled and inspected, no issues
```

Ask if the user wants to make any adjustments.
