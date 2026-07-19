# /generate_sop — Generate a Statement of Purpose

Generate an academic Statement of Purpose for a scholarship or program application.

`$ARGUMENTS` should identify the program, e.g.:
- `/generate_sop DAAD PhD Computer Science`
- `/generate_sop Fulbright MSc Data Science`
- `/generate_sop Stanford PhD Machine Learning`

---

## Step 0: Parse Input

Extract from `$ARGUMENTS`:
- Scholarship/program name
- Degree level
- Field of study

If insufficient info, ask the user for details.

---

## Step 1: Load Profile

Read `career_profile.json` for the full profile.
Pay special attention to:
- Education (degree, thesis, topics)
- Research interests (from `scholarship_goals.research_interests`)
- Publications
- Experience (research-related)

---

## Step 2: Build SOP

Generate a structured SOP with these sections:

### 1. Opening Hook (100-150 words)
- Start with a compelling moment or insight
- Connect personal motivation to research area
- State the research question or area of focus

### 2. Academic Background (150-200 words)
- Degrees, institutions, dates
- Relevant coursework and thesis
- Academic achievements

### 3. Research Experience (200-300 words)
- Research projects and methodologies
- Publications and presentations
- Skills developed through research

### 4. Why This Program (150-200 words)
- Program strengths and faculty alignment
- Research environment and resources
- How the program enables research goals

### 5. Future Goals (100-150 words)
- Short-term goals (during the program)
- Long-term career vision
- Impact on the field

---

## Step 3: Present SOP

```
## Statement of Purpose

**Program:** PhD in Computer Science — DAAD Research Grant
**Word count:** ~850 words

---

[Full SOP content here]

---

### Key Decisions
- Focused on research interests: Machine Learning, Healthcare AI
- Referenced thesis: "Deep Learning for Arabic NLP"
- Highlighted 2 publications for academic credibility
- Connected to DAAD's focus on international research collaboration
```

---

## Important Rules

1. **Academic but personal.** Not stiff corporate-speak, not casual.
2. **Specific, not generic.** Name the research area, the program, the skills.
3. **Never fabricate.** Only use actual profile data.
4. **Research interests drive the narrative.** Everything connects back to them.
5. **Word limit awareness.** Most SOPs are 500-1000 words. Adjust accordingly.
