# /find_jobs — Search for Jobs Matching Your Profile

You are searching for job opportunities that match the candidate's profile.

The user may provide a focus area as `$ARGUMENTS` (e.g., `/find_jobs data science` or `/find_jobs broad`).

---

## Step 0: Load Profile

Read `career_profile.json` to get the candidate's:
- Target roles
- Primary and secondary skills
- Domain expertise
- Location preferences

If the profile doesn't exist, tell the user to run `/setup` or `/import_cv` first.

---

## Step 1: Build Search Queries

From the profile, build targeted search queries:

**If focus area provided:**
- "{focus_area} jobs {city} {country}"
- "{focus_area} site:linkedin.com/jobs"

**If no focus area:**
- For each target role: "{role} jobs {city} {country}"
- For top skills: "{skill} jobs {city} {country}"

**If broad:**
- Include adjacent roles
- Include broader location searches

---

## Step 2: Search

Run WebSearch queries in parallel. For each query:
1. Use `WebSearch` with the query
2. Focus on postings from the last 14 days
3. Target the candidate's geographic area

Also try the Danish portal CLIs if the candidate is in Denmark:
```bash
cd .agents/skills/jobindex-search/cli && bun run src/cli.ts "{query}"
cd .agents/skills/jobnet-search/cli && bun run src/cli.ts "{query}"
```

---

## Step 3: Fetch & Parse

For each promising result:
1. Use `WebFetch` to retrieve the full job posting
2. Extract: title, company, location, URL, key requirements, deadline
3. Skip if already in `job_scraper/seen_jobs.json` or `job_search_tracker.csv`

---

## Step 4: Quick Fit Assessment

For each new job, do a rapid fit check:

**High match:** Role directly involves the candidate's core skills
**Medium match:** Role is adjacent to the candidate's experience
**Low match:** Role requires significant skills the candidate lacks

---

## Step 5: Present Results

```
## New Job Matches — YYYY-MM-DD

Found X new positions (Y high, Z medium, W low match).

| # | Fit | Title | Company | Location | Deadline | URL |
|---|-----|-------|---------|----------|----------|-----|
| 1 | 🟢 High | Data Scientist | Novo Nordisk | Copenhagen | 2026-07-01 | [Link](...) |
| 2 | 🟡 Medium | ML Engineer | Maersk | Copenhagen | 2026-06-20 | [Link](...) |

### High-Match Highlights

**1. Data Scientist at Novo Nordisk**
- ✅ Matches: Python, Machine Learning, Data Science
- 📋 Key requirements: 3+ years experience, scikit-learn, stakeholder communication
- 💡 Strong fit — aligns with target role and domain expertise

Want me to evaluate any of these in detail? Just give me the number(s).
```

---

## Step 6: Record Seen Jobs

Add all fetched jobs to `job_scraper/seen_jobs.json` for future deduplication.

---

## Important Rules

1. **Never fabricate job postings.** Only present jobs found via actual WebSearch/WebFetch results.
2. **Respect deduplication.** Always check seen_jobs.json AND job_search_tracker.csv before presenting.
3. **Focus on configured geographic area.** Skip jobs that require relocation.
4. **Only open positions.** Skip postings with expired deadlines.
5. **Be efficient with WebFetch.** Pre-filter using titles and snippets before fetching full pages.
