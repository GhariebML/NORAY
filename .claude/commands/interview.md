# /interview — Prepare for a Job Interview

You are generating comprehensive interview preparation for a specific role.

`$ARGUMENTS` should be the company name and role, e.g.:
- `/interview Novo Nordisk - Data Scientist`
- `/interview Google - ML Engineer`
- `/interview https://jobindex.dk/job/1234567`

---

## Step 0: Parse Input

If `$ARGUMENTS` is a URL, fetch the job posting.
If it's a company + role, read the application from the tracker or search for the posting.
If there's an existing CV/cover letter for this company, read them for context.

---

## Step 1: Load Profile

Read `career_profile.json` for the full candidate profile.
Also read `07-interview-prep.md` for the interview framework.

---

## Step 2: Generate STAR Examples

From the candidate's experience, create 5-7 STAR examples:

For each:
1. **Question** — the likely interview question
2. **Situation** — context from the candidate's actual experience
3. **Task** — what was required
4. **Action** — what the candidate specifically did
5. **Result** — measurable outcome

Map each example to:
- The skill it demonstrates
- Which interview questions it answers

Base ALL answers on actual profile data. Never fabricate experiences.

---

## Step 3: Generate Talking Points

Create key talking points organized by priority:

**High priority:**
- Skills that directly match the job requirements
- Most relevant experience
- Domain expertise alignment

**Medium priority:**
- Education background
- Projects that demonstrate relevant skills
- Soft skills mentioned in the posting

---

## Step 4: Generate Questions to Ask

Create 5-8 thoughtful questions for the candidate to ask:
- About success metrics for the role
- About team challenges and structure
- About professional development
- Role-specific questions (data infra for data roles, etc.)

---

## Step 5: Identify Gaps and Prepare Responses

Check the profile against job requirements and identify potential gap questions:
- Missing skills mentioned in the posting
- Short tenures or employment gaps
- Career pivots that need explanation

For each gap, provide:
- A response strategy (acknowledge + pivot + learn)
- Specific framing language

---

## Step 6: Generate Elevator Pitch

Create a 60-second "Tell me about yourself" answer:
- Current/most recent role
- Core expertise
- Top achievement
- Why this role/company

---

## Step 7: Present Preparation

Present the full preparation package in a clean format:

```
# Interview Preparation: Data Scientist at Novo Nordisk

## 🎤 Elevator Pitch
I'm a Data Scientist at Google with expertise in Python, Machine Learning,
and data pipeline development. My core achievement was building an ML
pipeline that reduced inference latency by 40%. I'm excited about this
role at Novo Nordisk because it combines my technical skills with my
interest in healthcare impact.

## ⭐ STAR Examples

### 1. "Tell me about a time you solved a complex technical problem."
**Skill:** Problem-solving, ML engineering
**S:** At Google, the ML inference pipeline had latency issues affecting user experience.
**T:** I was responsible for identifying bottlenecks and optimizing the pipeline.
**A:** Profiled the code, identified the preprocessing step as the bottleneck,
   implemented batch processing and caching.
**R:** Reduced inference latency by 40%, improving user satisfaction scores by 15%.

## 💬 Key Talking Points
- 🔴 Python + ML expertise directly matches their core requirements
- 🔴 Previous data science experience in similar industry
- 🟡 Stakeholder communication skills (mentioned in posting)

## ❓ Questions to Ask
1. What does success look like in this role in the first 6 months?
2. What are the biggest challenges the data team is currently facing?
3. What does the current data infrastructure look like?

## 🛡️ Gap Preparation
**Gap:** No direct pharma experience
**Strategy:** Acknowledge honestly, pivot to adjacent domain experience
**Framing:** "While I haven't worked in pharma directly, my experience in
healthcare data at Google gave me exposure to regulated data environments..."
```

Also save the full preparation to a file if requested.
