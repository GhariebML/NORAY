# /apply_scholarship — Generate Scholarship Application Materials

You are generating application materials for a specific scholarship.

`$ARGUMENTS` should identify the scholarship, e.g.:
- `/apply_scholarship DAAD`
- `/apply_scholarship Erasmus Mundus - MSc Data Science`
- `/apply_scholarship Chevening`

---

## Step 0: Identify Scholarship

If `$ARGUMENTS` matches a known portal, use that portal's info.
Otherwise, search for the scholarship via WebSearch.

Extract: scholarship name, provider, deadline, eligibility criteria, required materials.

---

## Step 1: Load Profile

Read `career_profile.json` for the full profile.
Read `scholarship_goals` section for research interests and target degrees.

---

## Step 2: Evaluate Eligibility

Score the candidate against the scholarship criteria:
- Nationality eligibility
- Degree level prerequisites
- Field of study match
- Language requirements
- GPA requirements
- Research interest alignment

Present the eligibility report with score and recommendations.

Ask: "You have a [score]% eligibility match. Should I proceed with generating application materials?"

---

## Step 3: Determine Required Materials

Based on the scholarship requirements, determine which documents to generate:

| Material | When Required |
|----------|---------------|
| SOP | Most academic scholarships (DAAD, Fulbright, Gates Cambridge, etc.) |
| Motivation Letter | European programs (Erasmus Mundus, Stipendium Hungaricum, etc.) |
| Research Proposal | PhD applications (Gates Cambridge, CSC, etc.) |
| Recommendation Drafts | Almost all scholarships |

---

## Step 4: Generate Materials

### 4a. Statement of Purpose (if required)
Generate an SOP with:
- Opening hook connecting personal motivation to research area
- Academic background and thesis details
- Research experience and publications
- Why this specific program/institution
- Future career goals and impact

Read the SOP template structure and tailor it to the scholarship.

### 4b. Motivation Letter (if required)
Generate a European-style motivation letter with:
- Personal motivation and story
- Academic and professional background
- Why this program
- What you will contribute
- Forward-looking closing

### 4c. Research Proposal (if required)
Generate a structured research proposal with:
- Title
- Introduction (research question + significance)
- Literature Review (current state + gaps)
- Methodology (approach + methods)
- Timeline (3-year PhD plan)
- Expected Outcomes
- Feasibility (why this candidate)

### 4d. Recommendation Letter Drafts (if required)
Generate draft recommendation letters for the candidate's referees:
- Academic supervisor version
- Employer version (if applicable)
- Each with [FILL IN] markers for personal anecdotes

---

## Step 5: Present Materials

```
## ✅ Scholarship Application Materials Ready

**Scholarship:** DAAD Research Grant
**Eligibility Score:** 85/100 (High match)
**Deadline:** 2026-10-15

### Generated Documents

1. **Statement of Purpose** (~800 words)
   - Sections: Opening hook, Academic background, Research experience, Why DAAD, Future goals
   - Key focus: Machine learning for healthcare applications

2. **Research Proposal** (~1500 words)
   - Title: "Advancing Healthcare Diagnostics Through Machine Learning"
   - Sections: Introduction, Literature review, Methodology, Timeline, Outcomes

3. **Recommendation Letter Draft** (2 letters)
   - Academic supervisor version — [FILL IN] markers for research anecdotes
   - Employer version — [FILL IN] markers for professional achievements

### Next Steps
- Review and personalize each document
- Fill in the [FILL IN] markers in recommendation drafts
- Have referees review and sign their letters
- Submit before the deadline: 2026-10-15

Want me to make any adjustments to these materials?
```

---

## Step 6: Track Application

Add the scholarship to the application tracker with:
- Status: "preparing"
- Documents generated
- Deadline
- Eligibility score

---

## Important Rules

1. **Never fabricate achievements.** All content must come from the actual profile.
2. **Tailor to the scholarship.** Each scholarship has different emphases — adapt accordingly.
3. **Academic tone for SOPs.** More formal than cover letters.
4. **Personal tone for motivation letters.** European-style, genuine and reflective.
5. **Research proposals need real references.** Use placeholder format: "[Author] (Year). Title. Journal."
6. **Recommendation drafts have [FILL IN] markers.** Make it clear what the referee needs to add.
