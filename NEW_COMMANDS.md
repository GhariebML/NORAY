# NORAY — Claude Code Commands Reference

All existing commands are preserved. New commands are added for the expanded platform.

## Existing Commands (Preserved)

| Command | Status | Module |
|---------|--------|--------|
| `/setup` | ✅ Preserved | `NORAY/profile_engine/` |
| `/scrape` | ✅ Preserved | `NORAY/career_agent/job_search.py` |
| `/apply <url>` | ✅ Preserved | `NORAY/career_agent/` pipeline |
| `/expand` | ✅ Preserved | `NORAY/profile_engine/github_importer.py` |
| `/upskill` | ✅ Preserved | `NORAY/upskill_agent/` |
| `/reset` | ✅ Preserved | `NORAY/dashboard/` |

## New Commands

### Profile Management

#### `/import_cv`
Import and parse a CV file into the career profile.
```
/import_cv path/to/cv.pdf
```
- Supports PDF, .tex, .docx
- Extracts structured data via LLM
- Merges into existing `career_profile.json`

#### `/import_linkedin`
Import LinkedIn profile export.
```
/import_linkedin path/to/linkedin.pdf
```
- Cross-references with existing CV data
- Detects and flags conflicts

#### `/import_certificates`
Import certificates and diplomas.
```
/import_certificates
```
- Scans `documents/diplomas/` folder
- Parses certificate PDFs and images
- Adds to `career_profile.json`

### Career Agent

#### `/find_jobs`
Alias for `/scrape` with additional filters.
```
/find_jobs
/find_jobs data science
/find_jobs broad
```

#### `/apply_job`
Alias for `/apply` — generates job application.
```
/apply_job https://jobindex.dk/job/1234567
```

#### `/interview`
Standalone interview preparation (without applying).
```
/interview Company Name - Role Title
```
- Generates STAR examples from profile
- Prepares talking points
- Suggests questions to ask

### Scholarship Agent

#### `/find_scholarships`
Discover scholarships matching the profile.
```
/find_scholarships
/find_scholarships PhD Germany
/find_scholarships Fulbright
```
- Searches multiple scholarship portals
- Scores eligibility
- Shows upcoming deadlines

#### `/apply_scholarship`
Generate scholarship application materials.
```
/apply_scholarship <scholarship_name_or_url>
```
- Evaluates eligibility
- Generates SOP, motivation letter, or research proposal
- Drafts recommendation letter outlines

#### `/generate_sop`
Generate a Statement of Purpose.
```
/generate_sop <program_name>
```
- Academic framing
- Research interest integration
- Tailored to specific program

#### `/generate_motivation`
Generate a motivation letter (European-style).
```
/generate_motivation <scholarship_name>
```
- Personal narrative + academic fit
- Formal but personal tone

#### `/generate_research`
Generate a research proposal for PhD/postdoc.
```
/generate_research <topic>
```
- Research question + methodology
- Literature review framing
- Timeline and feasibility

### Dashboard

#### `/dashboard`
View application tracking and analytics.
```
/dashboard
/dashboard jobs
/dashboard scholarships
/dashboard analytics
```
- Unified view of all applications
- Success rates and pipeline stats
- Upcoming deadlines
