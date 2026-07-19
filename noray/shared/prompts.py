"""
NORAY — Centralized Prompt Templates

All LLM prompt templates in one place.
Agents import prompts from here instead of reading skill files directly.
"""

# ─── Profile Extraction ───────────────────────────────────────

CV_EXTRACTION_PROMPT = """Extract structured career information from the following CV/resume content.

Return a JSON object with these fields:
- identity: name, email, phone, location (city, country), linkedin_url, github_url
- education: list of {degree, field, institution, start_year, end_year, thesis, gpa, topics}
- experience: list of {title, company, location, start_date, end_date, responsibilities, achievements, technologies}
- skills: {primary, secondary, domain, tools}
- certifications: list of {name, issuer, date}
- awards: list of {name, event, year, description}
- publications: list of {authors, title, journal, year, doi}

CV Content:
{cv_content}
"""

LINKEDIN_EXTRACTION_PROMPT = """Extract structured career information from the following LinkedIn profile export.

Return a JSON object with these fields:
- identity: name, email, linkedin_url
- about: full summary/about text
- experience: list of {title, company, location, start_date, end_date, responsibilities}
- education: list of {degree, field, institution, start_year, end_year}
- skills: list of skills with endorsement counts if visible
- certifications: list of {name, issuer, date}
- volunteer: list of {role, organization, description}

LinkedIn Content:
{linkedin_content}
"""

# ─── Job Application ──────────────────────────────────────────

FIT_EVALUATION_PROMPT = """Evaluate the following job posting against the candidate's profile.

## Job Posting
{job_posting}

## Candidate Profile
{candidate_profile}

## Evaluation Framework
Score each dimension (0-100):
1. **Skills Match** — required and preferred skills vs candidate's skills
2. **Experience Match** — work history relevance to the role
3. **Education Match** — degree level and field alignment
4. **Culture/Behavioral Fit** — work style alignment with role expectations
5. **Location Fit** — geographic compatibility

Return:
- Scores for each dimension
- Overall fit score (weighted average)
- Verdict: strong_fit / moderate_fit / weak_fit
- Key matching strengths (3-5 bullets)
- Key gaps to address (3-5 bullets)
- Recommendation: proceed / reconsider / skip
"""

CV_TAILORING_PROMPT = """Tailor the following CV for the specific job posting.

## Job Posting
{job_posting}

## Candidate Profile
{candidate_profile}

## Current CV
{current_cv}

## Instructions
1. Reframe the profile statement for this specific role
2. Reorder experience bullets by relevance to the posting
3. Emphasize skills and achievements that match job requirements
4. Use keywords from the posting naturally (for ATS optimization)
5. Keep to exactly 2 pages
6. Do NOT fabricate any skills or experience not in the original profile

Return the tailored LaTeX CV content.
"""

COVER_LETTER_PROMPT = """Write a targeted cover letter for the following job posting.

## Job Posting
{job_posting}

## Candidate Profile
{candidate_profile}

## Writing Style Rules
{writing_style}

## Template Structure
{cover_letter_template}

## Instructions
1. Match the language of the job posting
2. Open with a specific connection to the company/role
3. Highlight 2-3 most relevant experiences with concrete achievements
4. Address any gaps honestly by framing adjacent experience
5. Close with enthusiasm and a clear call to action
6. Keep to approximately 1 page
7. Do NOT fabricate any skills or experience

Return the LaTeX cover letter content using the cover.cls template.
"""

# ─── Scholarship Application ─────────────────────────────────

SOP_PROMPT = """Write a Statement of Purpose for the following scholarship/program.

## Scholarship/Program
{scholarship_info}

## Candidate Profile
{candidate_profile}

## Research Interests
{research_interests}

## Instructions
1. Open with a compelling hook about the research/academic interest
2. Connect academic background to the proposed field of study
3. Highlight relevant research experience and methodological skills
4. Explain why this specific program/institution is the right fit
5. Describe future career goals and how this program enables them
6. Maintain an academic but personal tone
7. Keep to 1-2 pages (depending on program requirements)

Return the SOP in markdown format.
"""

MOTIVATION_LETTER_PROMPT = """Write a motivation letter for the following scholarship/program.

## Scholarship/Program
{scholarship_info}

## Candidate Profile
{candidate_profile}

## Instructions
1. Open with personal motivation and background
2. Connect your experience to the program's goals
3. Highlight what makes you a strong candidate
4. Describe what you hope to achieve
5. Close with gratitude and forward-looking statement
6. European-style format (formal but personal)
7. Keep to 1 page

Return the motivation letter in markdown format.
"""

RESEARCH_PROPOSAL_PROMPT = """Write a research proposal for the following scholarship/program.

## Scholarship/Program
{scholarship_info}

## Candidate Profile
{candidate_profile}

## Research Interests
{research_interests}

## Instructions
1. Title: Clear, specific research title
2. Introduction: Research question and its significance
3. Literature Review: Brief overview of existing work and gaps
4. Methodology: Proposed approach and methods
5. Timeline: Realistic project timeline
6. Expected Outcomes: Contribution to the field
7. Feasibility: Why this candidate can deliver this research
8. References: Key citations (real papers only)

Return the research proposal in markdown format with clear section headers.
"""

RECOMMENDATION_DRAFT_PROMPT = """Draft a recommendation letter outline for the following candidate.

## Candidate Profile
{candidate_profile}

## Referee Context
- Relationship: {relationship}
- Tone: {tone}  # academic_supervisor, employer, colleague

## Instructions
1. Opening: Context of the relationship and how long you've known the candidate
2. Academic/Professional ability: Specific examples of excellence
3. Character traits: Personal qualities with evidence
4. Comparative assessment: How they rank among peers
5. Closing: Strong endorsement and contact invitation
6. Do NOT fabricate specific incidents — create outlines the referee should fill in

Return the recommendation letter draft with [FILL IN] markers for personal anecdotes.
"""

# ─── Interview Preparation ────────────────────────────────────

INTERVIEW_STAR_PROMPT = """Generate STAR-format interview preparation for the following role.

## Job Posting
{job_posting}

## Candidate Profile
{candidate_profile}

## Instructions
Generate 5-7 likely interview questions for this role and prepare STAR answers:

For each question:
1. **Question**: The likely interview question
2. **Situation**: Context from the candidate's actual experience
3. **Task**: What was required
4. **Action**: What the candidate specifically did
5. **Result**: Measurable outcome

Also generate:
- 3 questions the candidate should ask the interviewer
- Key talking points for "Tell me about yourself"
- Potential red flags to prepare for

Base all answers on actual profile data. Do NOT fabricate experiences.
"""

# ─── Skill Gap Analysis ──────────────────────────────────────

SKILL_GAP_PROMPT = """Analyze the skill gaps between the candidate profile and the target role(s).

## Candidate Profile
{candidate_profile}

## Target Requirements
{requirements}

## Instructions
1. Identify hard skills present in requirements but missing from profile
2. Identify soft skill gaps
3. Identify domain knowledge gaps
4. Identify tooling/process gaps
5. Identify credential/certification gaps
6. Prioritize: Critical > High > Medium > Low
7. Suggest study direction for each gap

Return a structured gap analysis with priorities and time estimates.
"""

CAREER_ROADMAP_PROMPT = """Build a career roadmap for the following candidate.

## Current Profile
{candidate_profile}

## Career Goals
{career_goals}

## Skill Gaps Identified
{skill_gaps}

## Instructions
Create a 6-24 month career roadmap with:
1. Monthly milestones
2. Learning priorities (ordered by impact and dependency)
3. Portfolio/project suggestions
4. Networking targets
5. Certification timeline
6. Application strategy (when to start applying for target roles)

Return the roadmap as a structured timeline with clear milestones.
"""
