# /import_github — Import GitHub Profile and Projects

You are importing GitHub profile data into the NORAY career profile system.

The user provides a GitHub username as `$ARGUMENTS`.

---

## Step 0: Determine Username

If `$ARGUMENTS` contains a username, use it directly.

If `$ARGUMENTS` is a URL (e.g., `https://github.com/username`), extract the username.

If `$ARGUMENTS` is empty, check the existing profile for a GitHub URL:
- Read `career_profile.json` → `identity.github_url`
- Extract username from the URL

If no username is found, ask the user.

---

## Step 1: Fetch GitHub Data

Use the GitHub API (no auth needed for public profiles):

```
GET https://api.github.com/users/{username}
GET https://api.github.com/users/{username}/repos?per_page=100&sort=updated
```

For each repo, also fetch:
- Languages: `GET https://api.github.com/repos/{owner}/{repo}/languages`
- README: `GET https://api.github.com/repos/{owner}/{repo}/readme`

Extract:
- User info: name, bio, company, location, blog
- Repos: name, description, language, languages, stars, topics, URL
- Aggregate: all languages used, total stars, top projects

---

## Step 2: Load Existing Profile

Read `career_profile.json`.

---

## Step 3: Map GitHub Data to Profile

### Projects
Map top repos (by stars/recency) to the `projects` section:
- Name: repo name
- Description: repo description
- Technologies: languages + topics
- URL: repo URL
- Highlights: star count, notable achievements

### Skills
Add discovered languages to `skills.tools`:
- Python, JavaScript, TypeScript, etc.

Add repo topics to `skills.domain`:
- machine-learning, web-development, data-science, etc.

### GitHub Section
Update the `github` section:
- Username
- Top repos
- Languages used
- Contribution highlights

---

## Step 4: Present Changes

```
## GitHub Import — Changes Detected

**Username:** GhariebML
**Public repos:** 15
**Languages:** Python, JavaScript, TypeScript, SQL
**Total stars:** 42

### New Projects
- [ ] ADPilot — AI-powered advertising optimization platform
  - Technologies: Python, FastAPI, Pydantic
  - ⭐ 12 stars
- [ ] AutoAnalyst-AI — Automated data analysis and insights
  - Technologies: Python, Jupyter, Pandas
  - ⭐ 8 stars

### New Skills (from GitHub)
- [ ] Tools: FastAPI, Jupyter, Docker
- [ ] Domain: data-science, machine-learning, advertising-tech

### Already Present
- Python ✓
- scikit-learn ✓
```

Wait for user confirmation.

---

## Step 5: Apply and Sync

After confirmation:
1. Backup existing profile
2. Add projects and skills to profile
3. Save `career_profile.json`
4. Sync legacy skill files

---

## Step 6: Report Results

```
## ✅ GitHub Import Complete

**Username:** GhariebML
**New data added:**
- 5 projects
- 4 tools/skills
- 3 domain areas

**Files updated:**
- career_profile.json
- 01-candidate-profile.md
```

---

## Important Rules

1. **Public repos only.** Don't try to access private repos.
2. **Skip forks.** Only import original repositories.
3. **Sort by quality.** Stars and recency matter more than repo count.
4. **Topics are domain signal.** GitHub topics reveal domain expertise.
5. **Respect rate limits.** GitHub API allows 60 requests/hour unauthenticated.
