from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from noray.models.chat import ChatMessageModel
from noray.database import SessionLocal

class ChatMemoryManager:
    """Manages short-term conversation context fetched from database."""
    def __init__(self, session_id: str):
        self.session_id = session_id

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, str]]:
        """Fetch latest N messages formatted for LLM system context."""
        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessageModel)
                .filter(ChatMessageModel.session_id == self.session_id)
                .order_by(ChatMessageModel.created_at.asc())
                .all()
            )
            
            # Keep only the last N messages
            recent = messages[-limit:] if len(messages) > limit else messages
            
            formatted = []
            for msg in recent:
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
            return formatted
        finally:
            db.close()

    def add_message(self, role: str, content: str, citations: Optional[List[Dict[str, Any]]] = None) -> None:
        """Saves a new chat message to database."""
        import uuid
        db = SessionLocal()
        try:
            msg = ChatMessageModel(
                id=str(uuid.uuid4()),
                session_id=self.session_id,
                role=role,
                content=content,
                citations=citations
            )
            db.add(msg)
            db.commit()
        finally:
            db.close()


class ProfileMemoryManager:
    """Manages user-profile context injection."""
    def __init__(self, profile_data: Dict[str, Any]):
        self.profile_data = profile_data

    def get_profile_summary_prompt(self) -> str:
        """Returns a summarized persona profile instruction string for prompt system messages."""
        identity = self.profile_data.get("identity", {})
        name = identity.get("name", "Candidate")
        email = identity.get("email", "")
        loc = identity.get("location", {})
        city = loc.get("city", "")
        country = loc.get("country", "")
        
        # Pull skills list
        skills = self.profile_data.get("skills", {})
        prim_skills = ", ".join(skills.get("primary", []))
        sec_skills = ", ".join(skills.get("secondary", []))
        
        summary = (
            f"You are helping the candidate: {name} (Email: {email}, Location: {city}, {country}).\n"
            f"Candidate Primary Skills: {prim_skills}\n"
            f"Candidate Secondary Skills: {sec_skills}\n"
        )
        return summary
