"""
NORAY — Confidence-Based Task Analyzer

Classifies user requests into task categories and recommends the optimal
model family for each task. Used by SmartRouter for confidence-based routing.
No LLM calls — pure keyword/pattern matching for sub-1ms classification.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("noray.llm.task_analyzer")


class TaskCategory(str, Enum):
    PROGRAMMING = "programming"
    CODE_EXPLANATION = "code_explanation"
    BUG_FIXING = "bug_fixing"
    SQL = "sql"
    LARGE_DOC_GENERATION = "large_doc_generation"
    RESEARCH = "research"
    MATH = "math"
    COMPLEX_REASONING = "complex_reasoning"
    LONG_CONTEXT = "long_context"
    CAREER_WRITING = "career_writing"
    CV = "cv"
    SCHOLARSHIPS = "scholarships"
    RAG_REASONING = "rag_reasoning"
    IMAGE_UNDERSTANDING = "image_understanding"
    GENERAL = "general"
    SUMMARIZATION = "summarization"
    CREATIVE_WRITING = "creative_writing"


@dataclass
class TaskAnalysis:
    category: TaskCategory
    confidence: float
    recommended_model_family: str
    requires_vision: bool = False
    requires_long_context: bool = False
    requires_coding: bool = False
    keywords_matched: list[str] = field(default_factory=list)
    explanation: str = ""


MODEL_ROUTING_MAP: dict[TaskCategory, str] = {
    TaskCategory.PROGRAMMING: "qwen2.5-coder",
    TaskCategory.CODE_EXPLANATION: "qwen2.5-coder",
    TaskCategory.BUG_FIXING: "qwen2.5-coder",
    TaskCategory.SQL: "qwen2.5-coder",
    TaskCategory.LARGE_DOC_GENERATION: "gemma",
    TaskCategory.RESEARCH: "gemma",
    TaskCategory.MATH: "gemma",
    TaskCategory.COMPLEX_REASONING: "gemma",
    TaskCategory.LONG_CONTEXT: "gemma",
    TaskCategory.CAREER_WRITING: "gemma",
    TaskCategory.CV: "gemma",
    TaskCategory.SCHOLARSHIPS: "gemma",
    TaskCategory.RAG_REASONING: "gemma",
    TaskCategory.IMAGE_UNDERSTANDING: "gemma",
    TaskCategory.GENERAL: "gemma",
    TaskCategory.SUMMARIZATION: "gemma",
    TaskCategory.CREATIVE_WRITING: "gemma",
}


TASK_PATTERNS: list[tuple[TaskCategory, list[str], float]] = [
    (TaskCategory.PROGRAMMING, [
        r"\bwrite\s+a\s+(\w+\s+)?(function|class|script|program|code|app|api|endpoint|route|module)\b",
        r"\bimplement\s+a\s+(\w+\s+)?(function|class|algorithm|feature|component)\b",
        r"\bcreate\s+a\s+(\w+\s+)?(function|class|script|program|rest api|api|endpoint|route)\b",
        r"\b(code|program)\s+(generation|writing|implementation|creation)\b",
        r"\b(write|generate|create)\s+code\s+(for|to|that)\b",
        r"\bgenerate\s+code\b",
        r"\b(library|framework|sdk|api)\s+(for|to|implementation)\b",
        r"\brefactor\s+(this|the|code)\b",
        r"\b(react|vue|angular|svelte|next\.?js|nuxt)\s+component\b",
        r"\b(type|interface|enum|generic)\s+definition\b",
        r"\bdecorator\b.*\bpython\b",
        r"\brecursive\s+(function|algorithm|solution)\b",
        r"\bregex\b",
    ], 0.95),
    (TaskCategory.CODE_EXPLANATION, [
        r"\bexplain\s+(this|the|how|what|why)\s+(code|function|script|program|line|algorithm)\b",
        r"\bwhat does this\s+(code|function|line|snippet|script)\s+(do|mean)\b",
        r"\bhow does\s+(this|the)\s+(code|function|algorithm)\s+work\b",
        r"\bwalk me through\s+(this|the)\s+code\b",
        r"\bbreak down\s+(this|the)\s+code\b",
        r"\b(code|function)\s+explanation\b",
        r"\b(code|logic)\s+review\b",
    ], 0.9),
    (TaskCategory.BUG_FIXING, [
        r"\bfix\s+(this|the|a|bug|error|issue|problem)\b",
        r"\bbug\s+(fix|repair|resolve|in|with)\b",
        r"\bdebug\s+(this|the|code|function|issue)\b",
        r"\berror\s+(in|at|on|occurred|message|handling)\b",
        r"\b(why|why is)\s+(this|the|my)\s+(code|function|app|program)\s+(not|failing|crashing|error)\b",
        r"\btroubleshoot\b",
        r"\bexception\s+(in|at|raised|thrown|handling)\b",
        r"\btraceback\b",
    ], 0.95),
    (TaskCategory.SQL, [
        r"\b(sql|query|database|table|schema|select|insert|update|delete|join|where|group by|order by|having)\b",
        r"\bcreate\s+(table|view|index|procedure|function|trigger)\b",
        r"\balter\s+(table|column|schema)\b",
        r"\bmigration\s+(script|file|sql)\b",
        r"\borm\s+(query|model|relation|schema)\b",
    ], 0.9),
    (TaskCategory.LARGE_DOC_GENERATION, [
        r"\b(generate|write|draft|create)\s+(a\s+)?(\w+\s+)?(report|document|article|paper|essay|proposal|manual|guide|whitepaper|documentation)\b",
        r"\blong\s+(form|document|article|report|content)\b",
        r"\bdocumentation\s+(for|of|about|covering)\b",
        r"\bextensive\s+(report|analysis|review|guide)\b",
    ], 0.85),
    (TaskCategory.RESEARCH, [
        r"\bresearch\s+(on|about|into|regarding|the|topic|question|paper)\b",
        r"\b(literature|paper|study)\s+(review|survey|analysis)\b",
        r"\binvestigate\b",
        r"\bwhat\s+(is|are|does|do|was|were)\s+(the\s+)?(latest|current|state of|research|findings|studies)\b",
        r"\bcompare\s+(and\s+)?contrast\b",
        r"\b(topic|subject|field)\s+(overview|summary|introduction)\b",
        r"\banalyze\s+(the\s+)?(research|data|findings|literature|results|topic)\b",
        r"\b(findings|results|conclusion)\s+(of|from|suggest|indicate|show)\b",
    ], 0.85),
    (TaskCategory.MATH, [
        r"\b(calculate|compute|solve|evaluate|find)\s+(the\s+)?(equation|formula|derivative|integral|limit|sum|product)\b",
        r"\b(mathematical|math|algebra|calculus|geometry|trigonometry|statistics|probability)\b",
        r"\bsolve\s+(for|the|this)\s+(x|equation|problem|inequality|system)\b",
        r"\b(equation|formula|expression|derivative|integral)\s+(for|to|that|of)\b",
        r"\bproof\s+(of|that|for|by|using)\b",
        r"\btheorem\b",
    ], 0.9),
    (TaskCategory.COMPLEX_REASONING, [
        r"\b(think|reason|analyze|evaluate)\s+(step\s+by\s+step|carefully|critically|deeply|about)\b",
        r"\bchain\s+of\s+thought\b",
        r"\b(critical|analytical|logical|strategic)\s+(thinking|analysis|reasoning)\b",
        r"\b(pros|cons|advantages|disadvantages|tradeoffs)\s+(and|of|between)\b",
        r"\bif\s+.*\bthen\s+.*\belse\b",
        r"\bwhat\s+(would|might|could|should)\s+(happen|occur|be|result)\s+if\b",
        r"\b(hypothetical|scenario|thought\s+experiment)\b",
        r"\banalyze\s+(the\s+)?(impact|effect|implications|relationship|correlation|tradeoffs?)\b",
    ], 0.9),
    (TaskCategory.CAREER_WRITING, [
        r"\b(cover\s+letter|coverletter|motivation\s+letter|statement\s+of\s+purpose|personal\s+statement)\b",
        r"\b(job|position|role|vacancy|opening)\s+(application|apply|applying|search)\b",
        r"\b(resume|CV|curriculum\s+vitae)\s+(tailor|optimize|write|create|draft|update)\b",
        r"\b(ats|applicant\s+tracking)\s+(optimize|friendly|score|keyword)\b",
        r"\bcareer\s+(advice|guidance|counseling|coaching|strategy|plan|path)\b",
        r"\binterview\s+(preparation|prep|tips|questions|mock|practice)\b",
    ], 0.95),
    (TaskCategory.CV, [
        r"\b(create|write|draft|build|make)\s+a\s+(\w+\s+)?(resume|CV|curriculum\s+vitae)\b",
        r"\b(resume|CV|curriculum\s+vitae)\s*(writing|building|format|template|example|sample|draft|generate|create|tailor)\b",
        r"\baccomplishment\s+(bullet|statement|point|line)\b",
        r"\b(professional|work)\s+(summary|profile|experience|history)\b",
        r"\b(education|skills|certification)\s+section\b",
    ], 0.9),
    (TaskCategory.SCHOLARSHIPS, [
        r"\b(scholarship|scholarships|fellowship|grant|funding)\b",
        r"\b(daad|chevening|fulbright|erasmus|rhodes|gates|cambridge|oxford)\s+(scholarship|program|application)\b",
        r"\b(study|research)\s+(abroad|overseas|international|funding)\b",
        r"\bscholarship\s+(essay|statement|application|deadline|criteria|eligibility)\b",
        r"\b(apply|applying)\s+(for\s+)?(a\s+)?(scholarship|fellowship)\b",
    ], 0.95),
    (TaskCategory.RAG_REASONING, [
        r"\b(search|find|look\s+up|retrieve|query)\s+(for\s+)?(information|knowledge|data|documents|context)\b",
        r"\bwhat\s+(does|did|is|are|was)\s+(the\s+)?(document|file|upload|context|knowledge|database)\s+(say|contain|mention|state)\b",
        r"\bbased\s+on\s+(the\s+)?(document|context|information|knowledge|file|upload|data)\b",
        r"\b(from|according\s+to)\s+(the\s+)?(document|context|source|file|knowledge)\b",
        r"\bsummarize\s+(the\s+)?(document|file|context|article|paper|knowledge)\b",
        r"\brag\s+(query|search|retrieval|pipeline)\b",
    ], 0.85),
    (TaskCategory.IMAGE_UNDERSTANDING, [
        r"\b(image|picture|photo|screenshot|diagram|chart|graph|figure)\s+(analysis|understanding|describe|explain|read)\b",
        r"\bwhat\s+(is|does|can you)\s+(in|see|shown|displayed|depicted)\s+(\w+\s+)?(this|the)\s+(image|picture|photo|screenshot|diagram|chart|graph|figure)\b",
        r"\b(image|picture|photo|screenshot|diagram|chart|graph)\s+(analysis|understanding|describe|explain|read|show|display|depict)\b",
        r"\bdescribe\s+(this|the)\s+(image|picture|photo|screenshot|diagram|chart)\b",
        r"\bextract\s+(text|information|data)\s+(from|in)\s+(image|picture|screenshot)\b",
        r"\b(ocr|optical\s+character\s+recognition)\b",
        r"\bvision\b",
    ], 0.9),
    (TaskCategory.SUMMARIZATION, [
        r"\bsummarize\s+(this|the|a|following|above|text|content|article|document|paper|chat|conversation)\b",
        r"\b(summary|synopsis|abstract|executive\s+summary|tl;dr|tl;dr)\s+(of|for)\b",
        r"\bgive\s+(me\s+)?(a\s+)?(brief|short|quick)\s+(summary|overview|recap)\b",
        r"\bcondense\s+(this|the)\b",
        r"\bkey\s+(points|takeaways|findings|insights)\s+(from|of)\b",
    ], 0.9),
    (TaskCategory.CREATIVE_WRITING, [
        r"\b(write|create|draft|compose)\s+(a\s+)?(\w+\s+)?(story|poem|poetry|essay|article|blog|post|newsletter|script)\b",
        r"\b(creative|narrative|fiction|nonfiction|storytelling)\s+(writing|piece|content)\b",
        r"\b(blog|article|newsletter)\s+(post|draft|outline|idea|topic)\b",
        r"\b(content|copy)\s+(writing|generation|creation|strategy)\b",
    ], 0.85),
]


class TaskAnalyzer:
    """Fast, keyword-based task classifier for confidence-based model routing."""

    def __init__(self):
        self._compiled_patterns: list[tuple[TaskCategory, list[re.Pattern], float]] = []
        for category, patterns, confidence in TASK_PATTERNS:
            compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
            self._compiled_patterns.append((category, compiled, confidence))

    def analyze(self, query: str, context: str | None = None) -> TaskAnalysis:
        """
        Analyze a user query and determine the task category and recommended model.
        Returns a TaskAnalysis with confidence score and routing suggestion.
        """
        combined = query
        if context:
            combined = f"{query} {context}"

        best_category = TaskCategory.GENERAL
        best_confidence = 0.0
        all_matched_keywords: list[str] = []

        for category, patterns, base_confidence in self._compiled_patterns:
            matched_keywords: list[str] = []
            for pattern in patterns:
                match = pattern.search(combined)
                if match:
                    matched_keywords.append(match.group(0))

            if matched_keywords:
                confidence = base_confidence * min(1.0, len(matched_keywords) * 0.3)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_category = category
                    all_matched_keywords = matched_keywords

        recommended_model = MODEL_ROUTING_MAP.get(best_category, "gemma")

        requires_vision = best_category == TaskCategory.IMAGE_UNDERSTANDING
        requires_long_context = best_category in (
            TaskCategory.LONG_CONTEXT, TaskCategory.LARGE_DOC_GENERATION,
            TaskCategory.COMPLEX_REASONING,
        )
        requires_coding = best_category in (
            TaskCategory.PROGRAMMING, TaskCategory.CODE_EXPLANATION,
            TaskCategory.BUG_FIXING, TaskCategory.SQL,
        )

        explanation = (
            f"Task classified as '{best_category.value}' with {best_confidence:.0%} confidence. "
            f"Recommended model: {recommended_model}. "
            f"Keywords: {', '.join(all_matched_keywords[:5])}"
        )

        return TaskAnalysis(
            category=best_category,
            confidence=best_confidence,
            recommended_model_family=recommended_model,
            requires_vision=requires_vision,
            requires_long_context=requires_long_context,
            requires_coding=requires_coding,
            keywords_matched=all_matched_keywords,
            explanation=explanation,
        )

    def get_preferred_model_for_task(self, query: str, context: str | None = None) -> str:
        """Quick helper: returns the recommended model family for a query."""
        analysis = self.analyze(query, context)
        return analysis.recommended_model_family

    def is_coding_task(self, query: str) -> bool:
        """Check if the query is a coding-related task."""
        analysis = self.analyze(query)
        return analysis.requires_coding


task_analyzer = TaskAnalyzer()
