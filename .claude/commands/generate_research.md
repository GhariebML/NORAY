# /generate_research — Generate a Research Proposal

Generate a research proposal for PhD or postdoc applications.

`$ARGUMENTS` should describe the research area, e.g.:
- `/generate_research Machine Learning for Healthcare`
- `/generate_research NLP for Arabic Text`
- `/generate_research "Computer Vision for Autonomous Systems"`

---

## Step 0: Parse Input

Extract from `$ARGUMENTS`:
- Research topic/area
- Any specific focus or constraints

---

## Step 1: Load Profile

Read `career_profile.json` for:
- Research interests (from `scholarship_goals.research_interests`)
- Education and thesis
- Publications
- Technical skills
- Experience

---

## Step 2: Build Research Proposal

Generate a structured proposal:

### 1. Title
- Clear, specific, descriptive
- Include main topic and approach

### 2. Introduction (200-300 words)
- Research question or problem
- Significance and relevance
- Context and background
- Objectives
- Expected contribution

### 3. Literature Review (300-400 words)
- Current state of knowledge
- Key theories and frameworks
- Gaps in existing research
- How your research addresses these gaps

### 4. Methodology (200-300 words)
- Research design (qualitative, quantitative, mixed)
- Data collection methods
- Analysis techniques
- Validity and reliability measures
- Ethical considerations

### 5. Timeline (100-150 words)
- Year 1: Foundation (literature review, pilot study, data collection Phase 1)
- Year 2: Core Research (data collection Phase 2, analysis, synthesis)
- Year 3: Completion (writing, revision, defense)

### 6. Expected Outcomes (100-150 words)
- Contributions to the field
- Planned publications
- Practical impact

### 7. Feasibility (100-150 words)
- Why you are the right person
- Relevant skills and experience
- Preliminary work
- Potential challenges and mitigation

### 8. References
- 5-8 placeholder references in proper academic format
- Use: "[Author] (Year). Title. Journal."

---

## Step 3: Present

```
## Research Proposal

**Title:** Advancing Healthcare Diagnostics Through Machine Learning
**Word count:** ~1,500 words
**Sections:** 8

---

### Title
[Title content]

### 1. Introduction
[Introduction content]

### 2. Literature Review
[Literature review content]

...

### 8. References
1. [Author] (Year). A foundational study on ML for healthcare. [Journal].
2. [Author] (Year). Recent advances in medical AI. [Journal].
...

---

### Key Decisions
- Focused on ML for healthcare (from research interests)
- Used mixed-methods approach
- Structured as 3-year PhD timeline
- Referenced existing publications for credibility
```

---

## Important Rules

1. **Academic rigor.** Follow proper research proposal conventions.
2. **Specific research question.** Not too broad, not too narrow.
3. **Real gaps.** The literature review should identify genuine gaps.
4. **Feasible methodology.** Match methods to the candidate's skills.
5. **Placeholder references.** Use "[Author] (Year)" format — the user fills in real references.
6. **Adjustable timeline.** Note that the 3-year structure can be adapted for different programs.
