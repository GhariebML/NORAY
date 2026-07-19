# /find_scholarships — Discover Scholarships Matching Your Profile

You are searching for scholarship opportunities that match the candidate's profile.

`$ARGUMENTS` can be:
- Empty (search all matching scholarships)
- A degree level: `/find_scholarships PhD`
- A country: `/find_scholarships Germany`
- Both: `/find_scholarships MSc UK`
- A specific portal: `/find_scholarships DAAD`

---

## Step 0: Load Profile

Read `career_profile.json` to get the candidate's:
- Education (degree level, field)
- Nationality/country
- Languages
- Research interests (from scholarship_goals)
- Career goals

If the profile doesn't exist, tell the user to run `/setup` first.

---

## Step 1: Build Search Strategy

From the profile and arguments, determine:

**Target degree level:** From arguments or `scholarship_goals.target_degrees`
**Target country:** From arguments or `scholarship_goals.target_countries`
**Research area:** From `scholarship_goals.research_interests`
**Nationality:** From `identity.location.country`

Build search queries:
- "{degree} scholarship {country} {nationality} students 2026 fully funded"
- "PhD scholarship {research_area} fully funded 2026"
- "scholarships for {nationality} students 2026"

---

## Step 2: Search Portals and Web

### Known Portals
Check these portals against the target degree and country:
- DAAD (Germany) — MSc, PhD, PostDoc
- Chevening (UK) — MSc
- Fulbright (USA) — MSc, PhD
- Erasmus Mundus (EU) — MSc
- Commonwealth (UK) — MSc, PhD
- Gates Cambridge (UK) — PhD, PostDoc
- Rhodes (UK) — MSc, PhD
- Schwarzman (China) — MSc
- Mastercard Foundation (Africa) — BSc, MSc
- Türkiye Bursları (Turkey) — BSc, MSc, PhD
- MEXT (Japan) — MSc, PhD
- CSC (China) — MSc, PhD
- Stipendium Hungaricum (Hungary) — BSc, MSc, PhD

### Web Search
Run WebSearch queries for each generated search query.
Look for:
- Application deadlines
- Eligibility criteria
- Funding details
- Required application materials

---

## Step 3: Score Eligibility

For each discovered scholarship, score the candidate's eligibility:

**Check:**
- Nationality eligibility
- Degree level prerequisites
- Field of study match
- Language requirements
- GPA requirements
- Research interest alignment

**Score each criterion:**
- Met: 100 points
- Partially met: 50 points
- Not met: 0 points

**Overall score = average of all criteria**

**Determine fit level:**
- 70+: High match
- 40-69: Medium match
- <40: Low match

---

## Step 4: Present Results

```
## Scholarship Matches — YYYY-MM-DD

Found X scholarships (Y high, Z medium, W low match).

| # | Fit | Scholarship | Country | Degree | Deadline | Funding | URL |
|---|-----|-------------|---------|--------|----------|---------|-----|
| 1 | 🟢 High | DAAD | Germany | MSc/PhD | 2026-10-15 | Fully funded | [Link](...) |
| 2 | 🟢 High | Erasmus Mundus | EU | MSc | 2026-01-31 | Fully funded | [Link](...) |
| 3 | 🟡 Medium | Chevening | UK | MSc | 2026-11-02 | Fully funded | [Link](...) |

### High-Match Highlights

**1. DAAD Scholarship**
- ✅ Eligibility: Egyptian nationality eligible
- ✅ Degree: Offers PhD funding
- ✅ Field: Computer Science is a supported field
- 📋 Requires: SOP, 2 recommendation letters, research proposal
- 💡 Strong fit — aligns with target country and research interests

**2. Erasmus Mundus**
- ✅ Eligibility: International students eligible
- ✅ Degree: MSc programs available
- 📋 Requires: Motivation letter, CV, 2 recommendation letters
- 💡 Good fit — multiple EU universities, diverse programs
```

Ask: "Want me to help you apply to any of these? Give me the number(s)."

---

## Step 5: Record and Track

Add all discovered scholarships to `data/seen_scholarships.json`.
If the user decides to apply, add to the scholarship tracker.

---

## Important Rules

1. **Never fabricate scholarships.** Only present real opportunities from actual search results.
2. **Check deadlines.** Only show scholarships with future deadlines.
3. **Be honest about eligibility.** If the candidate doesn't meet a criterion, say so.
4. **Include required materials.** Always list what the scholarship requires (SOP, motivation, recommendations, etc.).
5. **Respect deduplication.** Check `data/seen_scholarships.json` before presenting.
