"""
NORAY — Professional Response Builder
Formats raw text into structured envelopes containing markdown, citations, confidence, and actions.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("noray.llm.response")


class ResponseBuilder:
    """Aggregates LLM outputs with traces, confidence, artifacts, and actions into structured JSON responses."""
    
    @staticmethod
    def build_structured_response(
        raw_content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        confidence_score: float = 0.95,
        reasoning_steps: Optional[List[str]] = None,
        suggested_actions: Optional[List[str]] = None,
        generated_artifacts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes markdown headings, metadata blocks, source lists and suggestions.
        """
        # Format reasoning traces
        reasoning_summary = ""
        if reasoning_steps:
            reasoning_summary = "### Reasoning Summary\n" + "\n".join([f"- {step}" for step in reasoning_steps])

        # Format action milestones
        actions_md = ""
        if suggested_actions:
            actions_md = "\n\n### Suggested Next Actions\n" + "\n".join([f"- [ ] {action}" for action in suggested_actions])

        # Format source citations list
        citations_md = ""
        if citations:
            citations_md = "\n\n### Sources & Citations\n" + "\n".join(
                [f"- [{i+1}] {c.get('source', 'Unknown')} (Relevance: {c.get('score', 0.0):.2f})" 
                 for i, c in enumerate(citations)]
            )

        # Assemble unified markdown body
        formatted_md = raw_content
        if reasoning_summary:
            formatted_md = f"{formatted_md}\n\n---\n\n{reasoning_summary}"
        if citations_md:
            formatted_md = f"{formatted_md}\n\n{citations_md}"
        if actions_md:
            formatted_md = f"{formatted_md}\n\n{actions_md}"

        return {
            "response": formatted_md,
            "confidence_score": confidence_score,
            "citations": citations or [],
            "reasoning_steps": reasoning_steps or [],
            "suggested_actions": suggested_actions or [],
            "generated_artifacts": generated_artifacts or []
        }
    
    @staticmethod
    def format_job_match(score: int, title: str, company: str, missing_skills: List[str], generated_cv: bool = False, generated_cl: bool = False) -> str:
        """Helper to create a beautiful structured job match evaluation report in markdown."""
        cv_status = "✅ Generated (Ready for download)" if generated_cv else "❌ Missing"
        cl_status = "✅ Generated (Ready for download)" if generated_cl else "❌ Missing"
        
        skills_md = ", ".join([f"`{s}`" for s in missing_skills]) if missing_skills else "*None! Perfect match.*"
        
        return f"""
# Job Match Evaluation
### **{title}** at **{company}**

| Parameter | Match Score |
|---|---|
| **Overall Fit** | **{score}%** |

### 🛠️ Missing Skill Gaps
{skills_md}

### 📄 Application Materials
* **CV**: {cv_status}
* **Cover Letter**: {cl_status}

---
### 🚀 Next Step
Click **Apply** to package your tailored documents and complete the submission workflow.
"""
