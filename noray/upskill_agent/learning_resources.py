"""
NORAY — Learning Resources

Find and recommend learning resources for skill gaps via web search.
Provides curated resource databases and personalized recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearningResource:
    """A recommended learning resource."""
    name: str = ""
    url: str = ""
    resource_type: str = ""  # course, book, tutorial, documentation, certification
    provider: str = ""  # Coursera, Udemy, etc.
    estimated_hours: int = 0
    difficulty: str = ""  # beginner, intermediate, advanced
    reason: str = ""  # why this resource fits
    rating: str = ""
    free: bool = True
    language: str = "English"


@dataclass
class LearningPlan:
    """A complete learning plan for a skill gap."""
    skill: str = ""
    resources: list[LearningResource] = field(default_factory=list)
    study_direction: str = ""
    total_hours: int = 0
    suggested_order: int = 0
    prerequisites: list[str] = field(default_factory=list)
    milestones: list[str] = field(default_factory=list)


# Curated resource database
_RESOURCE_DB: dict[str, list[dict]] = {
    "python": [
        {"name": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com", "type": "book", "provider": "Free Online", "hours": 40, "difficulty": "beginner", "free": True},
        {"name": "Python for Data Science and Machine Learning Bootcamp", "url": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/", "type": "course", "provider": "Udemy", "hours": 25, "difficulty": "intermediate", "free": False},
        {"name": "Real Python Tutorials", "url": "https://realpython.com", "type": "tutorial", "provider": "Real Python", "hours": 50, "difficulty": "intermediate", "free": True},
    ],
    "machine learning": [
        {"name": "Machine Learning Specialization", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "type": "course", "provider": "Coursera", "hours": 80, "difficulty": "beginner", "free": True},
        {"name": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow", "url": "https://www.oreilly.com/library/view/hands-on-machine-learning/9781098125967/", "type": "book", "provider": "O'Reilly", "hours": 60, "difficulty": "intermediate", "free": False},
        {"name": "Fast.ai Practical Deep Learning", "url": "https://course.fast.ai", "type": "course", "provider": "fast.ai", "hours": 50, "difficulty": "intermediate", "free": True},
    ],
    "deep learning": [
        {"name": "Deep Learning Specialization", "url": "https://www.coursera.org/specializations/deep-learning", "type": "course", "provider": "Coursera", "hours": 120, "difficulty": "intermediate", "free": True},
        {"name": "Deep Learning with PyTorch", "url": "https://www.pytorch.org/tutorials/", "type": "tutorial", "provider": "PyTorch", "hours": 40, "difficulty": "intermediate", "free": True},
        {"name": "d2l.ai (Dive into Deep Learning)", "url": "https://d2l.ai", "type": "book", "provider": "d2l.ai", "hours": 80, "difficulty": "intermediate", "free": True},
    ],
    "nlp": [
        {"name": "Stanford CS224N: NLP with Deep Learning", "url": "https://web.stanford.edu/class/cs224n/", "type": "course", "provider": "Stanford", "hours": 80, "difficulty": "advanced", "free": True},
        {"name": "NLP Specialization", "url": "https://www.coursera.org/specializations/natural-language-processing", "type": "course", "provider": "Coursera (deeplearning.ai)", "hours": 60, "difficulty": "intermediate", "free": True},
        {"name": "Hugging Face NLP Course", "url": "https://huggingface.co/learn/nlp-course", "type": "course", "provider": "Hugging Face", "hours": 40, "difficulty": "intermediate", "free": True},
    ],
    "pytorch": [
        {"name": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/", "type": "tutorial", "provider": "PyTorch", "hours": 30, "difficulty": "beginner", "free": True},
        {"name": "PyTorch Lightning Tutorials", "url": "https://lightning.ai/docs/pytorch/stable/", "type": "tutorial", "provider": "Lightning AI", "hours": 20, "difficulty": "intermediate", "free": True},
    ],
    "tensorflow": [
        {"name": "TensorFlow Official Tutorials", "url": "https://www.tensorflow.org/tutorials", "type": "tutorial", "provider": "Google", "hours": 30, "difficulty": "beginner", "free": True},
        {"name": "TensorFlow Developer Certificate", "url": "https://www.tensorflow.org/certificate", "type": "certification", "provider": "Google", "hours": 80, "difficulty": "intermediate", "free": False},
    ],
    "docker": [
        {"name": "Docker Official Getting Started", "url": "https://docs.docker.com/get-started/", "type": "tutorial", "provider": "Docker", "hours": 10, "difficulty": "beginner", "free": True},
        {"name": "Docker Deep Dive", "url": "https://www.udemy.com/course/docker-deep-dive/", "type": "course", "provider": "Udemy (Nigel Poulton)", "hours": 15, "difficulty": "intermediate", "free": False},
        {"name": "KodeKloud Docker Course", "url": "https://kodekloud.com/courses/docker-for-the-absolute-beginner/", "type": "course", "provider": "KodeKloud", "hours": 12, "difficulty": "beginner", "free": False},
    ],
    "go": [
        {"name": "Go Tour", "url": "https://go.dev/tour/", "type": "tutorial", "provider": "Go Dev", "hours": 10, "difficulty": "beginner", "free": True},
        {"name": "Effective Go", "url": "https://go.dev/doc/effective_go", "type": "tutorial", "provider": "Go Dev", "hours": 15, "difficulty": "intermediate", "free": True},
        {"name": "Go by Example", "url": "https://gobyexample.com", "type": "tutorial", "provider": "Go by Example", "hours": 20, "difficulty": "beginner", "free": True},
    ],
    "rust": [
        {"name": "The Rust Book", "url": "https://doc.rust-lang.org/book/", "type": "book", "provider": "Rust Lang", "hours": 40, "difficulty": "beginner", "free": True},
        {"name": "Rustlings Exercises", "url": "https://github.com/rust-lang/rustlings", "type": "tutorial", "provider": "Rust Lang", "hours": 20, "difficulty": "beginner", "free": True},
    ],
    "system design": [
        {"name": "System Design Interview (Alex Xu)", "url": "https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF", "type": "book", "provider": "Alex Xu", "hours": 30, "difficulty": "intermediate", "free": False},
        {"name": "Grokking System Design", "url": "https://www.designgurus.io/course/grokking-the-system-design-interview", "type": "course", "provider": "DesignGurus", "hours": 40, "difficulty": "intermediate", "free": False},
    ],
    "kubernetes": [
        {"name": "Kubernetes Official Tutorials", "url": "https://kubernetes.io/docs/tutorials/", "type": "tutorial", "provider": "Kubernetes", "hours": 20, "difficulty": "intermediate", "free": True},
        {"name": "CKA Certification Prep", "url": "https://kodekloud.com/courses/certified-kubernetes-administrator-cka/", "type": "course", "provider": "KodeKloud", "hours": 60, "difficulty": "advanced", "free": False},
    ],
    "aws": [
        {"name": "AWS Cloud Practitioner Essentials", "url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/cloud-practitioner-essentials", "type": "course", "provider": "AWS", "hours": 20, "difficulty": "beginner", "free": True},
        {"name": "AWS Solutions Architect Associate", "url": "https://www.udemy.com/course/aws-certified-solutions-architect-associate-saa-c03/", "type": "course", "provider": "Udemy (Stephane Maarek)", "hours": 40, "difficulty": "intermediate", "free": False},
    ],
    "sql": [
        {"name": "SQLBolt Interactive Tutorial", "url": "https://sqlbolt.com", "type": "tutorial", "provider": "SQLBolt", "hours": 10, "difficulty": "beginner", "free": True},
        {"name": "Mode Analytics SQL Tutorial", "url": "https://mode.com/sql-tutorial/", "type": "tutorial", "provider": "Mode", "hours": 15, "difficulty": "beginner", "free": True},
        {"name": "LeetCode Database Problems", "url": "https://leetcode.com/problemset/database/", "type": "tutorial", "provider": "LeetCode", "hours": 30, "difficulty": "intermediate", "free": True},
    ],
    "data science": [
        {"name": "IBM Data Science Professional Certificate", "url": "https://www.coursera.org/professional-certificates/ibm-data-science", "type": "certification", "provider": "Coursera (IBM)", "hours": 100, "difficulty": "beginner", "free": True},
        {"name": "Kaggle Learn", "url": "https://www.kaggle.com/learn", "type": "tutorial", "provider": "Kaggle", "hours": 30, "difficulty": "beginner", "free": True},
        {"name": "DataCamp Data Scientist Track", "url": "https://www.datacamp.com/tracks/data-scientist-with-python", "type": "course", "provider": "DataCamp", "hours": 90, "difficulty": "intermediate", "free": False},
    ],
    "git": [
        {"name": "Pro Git Book", "url": "https://git-scm.com/book/en/v2", "type": "book", "provider": "Git SCM", "hours": 15, "difficulty": "beginner", "free": True},
        {"name": "Learn Git Branching", "url": "https://learngitbranching.js.org", "type": "tutorial", "provider": "Learn Git Branching", "hours": 8, "difficulty": "beginner", "free": True},
    ],
    "leadership": [
        {"name": "The Manager's Path", "url": "https://www.oreilly.com/library/view/the-managers-path/9781491973882/", "type": "book", "provider": "O'Reilly", "hours": 15, "difficulty": "intermediate", "free": False},
        {"name": "High Output Management", "url": "https://www.oreilly.com/library/view/high-output-management/9780679760474/", "type": "book", "provider": "Vintage", "hours": 10, "difficulty": "intermediate", "free": False},
    ],
    "communication": [
        {"name": "Crucial Conversations", "url": "https://www.cruciallearning.com/crucial-conversations", "type": "book", "provider": "Crucial Learning", "hours": 8, "difficulty": "beginner", "free": False},
        {"name": "The Art of Explanation", "url": "https://www.amazon.com/Art-Explanation-Making-Things-Understand/dp/1477280375", "type": "book", "provider": "Lee LeFever", "hours": 6, "difficulty": "beginner", "free": False},
    ],
    "fastapi": [
        {"name": "FastAPI Official Tutorial", "url": "https://fastapi.tiangolo.com/tutorial/", "type": "tutorial", "provider": "FastAPI", "hours": 15, "difficulty": "intermediate", "free": True},
        {"name": "Test-Driven Development with FastAPI", "url": "https://testdriven.io/courses/fastapi-fundamentals/", "type": "course", "provider": "TestDriven.io", "hours": 20, "difficulty": "intermediate", "free": False},
    ],
    "react": [
        {"name": "React Official Tutorial", "url": "https://react.dev/learn", "type": "tutorial", "provider": "React", "hours": 20, "difficulty": "beginner", "free": True},
        {"name": "Full Stack Open (React section)", "url": "https://fullstackopen.com/en/part7", "type": "course", "provider": "University of Helsinki", "hours": 30, "difficulty": "intermediate", "free": True},
    ],
}


def find_resources(
    skill: str,
    current_level: str = "beginner",
    preferred_format: str = "",
) -> LearningPlan:
    """
    Find learning resources for a specific skill gap.

    Args:
        skill: The skill to learn
        current_level: Current proficiency level
        preferred_format: Preferred learning format (course, book, tutorial)

    Returns:
        LearningPlan with curated resources
    """
    plan = LearningPlan(skill=skill)

    # Get resources from curated database
    resources = _RESOURCE_DB.get(skill.lower(), [])

    # Filter by preferred format if specified
    if preferred_format:
        resources = [r for r in resources if r["type"] == preferred_format]

    # Build LearningResource objects
    for res in resources:
        plan.resources.append(LearningResource(
            name=res["name"],
            url=res["url"],
            resource_type=res["type"],
            provider=res["provider"],
            estimated_hours=res["hours"],
            difficulty=res["difficulty"],
            reason=_get_resource_reason(res, current_level),
            free=res.get("free", True),
        ))

    # Sort by difficulty progression (beginner first)
    difficulty_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    plan.resources.sort(key=lambda r: difficulty_order.get(r.difficulty, 1))

    # Calculate total hours
    plan.total_hours = sum(r.estimated_hours for r in plan.resources)

    # Set prerequisites
    plan.prerequisites = _get_prerequisites(skill)

    # Set milestones
    plan.milestones = _get_learning_milestones(skill, current_level)

    return plan


def suggest_study_order(plans: list[LearningPlan]) -> list[LearningPlan]:
    """
    Suggest an optimal study order for multiple learning plans.

    Rules:
    1. Dependencies first
    2. Critical before High before Medium
    3. Quick wins early
    4. Domain knowledge last
    """
    # Define dependency order
    dependency_order = {
        "python": 0,
        "sql": 0,
        "git": 0,
        "machine learning": 1,
        "deep learning": 2,
        "nlp": 2,
        "pytorch": 1,
        "tensorflow": 1,
        "data science": 1,
        "docker": 1,
        "kubernetes": 2,
        "aws": 2,
        "leadership": 3,
        "communication": 3,
    }

    def sort_key(plan: LearningPlan) -> tuple[int, int]:
        order = dependency_order.get(plan.skill.lower(), 2)
        # Prefer shorter plans early (quick wins)
        return (order, plan.total_hours)

    return sorted(plans, key=sort_key)


def _get_resource_reason(resource: dict, current_level: str) -> str:
    """Generate a reason why this resource fits."""
    rtype = resource["type"]
    difficulty = resource["difficulty"]
    provider = resource["provider"]

    if difficulty == current_level:
        reason = f"Matches your current level ({current_level})"
    elif difficulty == "beginner":
        reason = "Good foundation builder"
    elif difficulty == "advanced":
        reason = "Advanced material to push your skills further"
    else:
        reason = "Intermediate level — step up from basics"

    if rtype == "course":
        return f"{reason}. Structured course from {provider}."
    elif rtype == "book":
        return f"{reason}. Comprehensive reference material."
    elif rtype == "tutorial":
        return f"{reason}. Hands-on tutorial format."
    return reason


def _get_prerequisites(skill: str) -> list[str]:
    """Get prerequisites for a skill."""
    prereqs = {
        "machine learning": ["python", "linear algebra basics"],
        "deep learning": ["machine learning", "python"],
        "nlp": ["deep learning", "python"],
        "pytorch": ["python", "machine learning basics"],
        "tensorflow": ["python", "machine learning basics"],
        "go": [
        {"name": "Go Tour", "url": "https://go.dev/tour/", "type": "tutorial", "provider": "Go Dev", "hours": 10, "difficulty": "beginner", "free": True},
        {"name": "Effective Go", "url": "https://go.dev/doc/effective_go", "type": "tutorial", "provider": "Go Dev", "hours": 15, "difficulty": "intermediate", "free": True},
        {"name": "Go by Example", "url": "https://gobyexample.com", "type": "tutorial", "provider": "Go by Example", "hours": 20, "difficulty": "beginner", "free": True},
    ],
    "rust": [
        {"name": "The Rust Book", "url": "https://doc.rust-lang.org/book/", "type": "book", "provider": "Rust Lang", "hours": 40, "difficulty": "beginner", "free": True},
        {"name": "Rustlings Exercises", "url": "https://github.com/rust-lang/rustlings", "type": "tutorial", "provider": "Rust Lang", "hours": 20, "difficulty": "beginner", "free": True},
    ],
    "system design": [
        {"name": "System Design Interview (Alex Xu)", "url": "https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF", "type": "book", "provider": "Alex Xu", "hours": 30, "difficulty": "intermediate", "free": False},
        {"name": "Grokking System Design", "url": "https://www.designgurus.io/course/grokking-the-system-design-interview", "type": "course", "provider": "DesignGurus", "hours": 40, "difficulty": "intermediate", "free": False},
    ],
    "kubernetes": ["docker"],
        "aws": ["networking basics"],
        "data science": ["python", "sql", "statistics basics"],
    }
    return prereqs.get(skill.lower(), [])


def _get_learning_milestones(skill: str, current_level: str) -> list[str]:
    """Get milestone checkpoints for a learning plan."""
    milestones = {
        "python": ["Complete first script", "Build a CLI tool", "Write a web scraper", "Contribute to open source"],
        "machine learning": ["Understand supervised learning", "Build first model", "Master evaluation metrics", "Complete Kaggle notebook"],
        "deep learning": ["Understand backpropagation", "Build a neural network", "Train a CNN", "Deploy a model"],
        "nlp": ["Tokenize text", "Build a classifier", "Fine-tune a transformer", "Build a chatbot"],
        "docker": ["Run first container", "Write a Dockerfile", "Compose multi-container app", "Deploy to cloud"],
        "data science": ["EDA on real dataset", "Build a prediction model", "Create a dashboard", "Complete end-to-end project"],
    }
    return milestones.get(skill.lower(), ["Complete tutorials", "Build practice project", "Apply in real scenario"])
