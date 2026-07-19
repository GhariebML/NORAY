# /generate_motivation — Generate a Motivation Letter

Generate a European-style motivation letter for a scholarship or program application.

`$ARGUMENTS` should identify the program, e.g.:
- `/generate_motivation Erasmus Mundus MSc`
- `/generate_motivation Stipendium Hungaricum`
- `/generate_motivation Mastercard Foundation`

---

## Step 0: Parse Input

Extract from `$ARGUMENTS`:
- Scholarship/program name
- Degree level (if mentioned)
- Country (if mentioned)

---

## Step 1: Load Profile

Read `career_profile.json` for the full profile.

---

## Step 2: Build Motivation Letter

Generate a structured letter with:

### 1. Personal Motivation (100-150 words)
- What drives you personally
- A specific moment that shaped your direction
- Connection to the field

### 2. Background (100-150 words)
- Academic background
- Professional experience
- Relevant skills

### 3. Why This Program (100-150 words)
- What attracts you to this specific program
- Country/institution if relevant
- Connection to your goals

### 4. What I Will Contribute (100 words)
- Unique perspective or skills
- How you'll enrich the community

### 5. Closing (50-100 words)
- Reaffirm enthusiasm
- Express gratitude
- Forward-looking statement

---

## Step 3: Present

```
## Motivation Letter

**Program:** Erasmus Mundus MSc in Data Science
**Word count:** ~450 words

---

[Full motivation letter content here]

---

### Key Decisions
- Connected personal motivation to career goals
- Emphasized international study experience
- Highlighted technical skills for program contribution
```

---

## Important Rules

1. **More personal than an SOP.** Share your story and motivation genuinely.
2. **European style.** Formal but personal, not corporate.
3. **Specific to the program.** Show you've researched it.
4. **Genuine enthusiasm.** Not generic "I am passionate about..."
5. **Keep it concise.** Most motivation letters are 400-600 words.
