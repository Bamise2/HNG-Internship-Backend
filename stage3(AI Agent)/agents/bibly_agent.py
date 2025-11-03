# agents/bibly_agent.py
from typing import Optional, List
from models.a2a import A2AMessage, MessagePart, TaskResult, TaskStatus, Artifact
from uuid import uuid4
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_verses(topic: str) -> list:
    """Fetch Bible verses from Bible SuperSearch API"""
    api_url = f"https://api.biblesupersearch.com/api?bible=kjv&search={topic}&whole_word=on"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            
            # Filter and sanitize
            clean_results = []
            for v in results:
                if not isinstance(v, dict):
                    continue
                if not v.get("book_name") or not v.get("chapter_verse"):
                    continue
                clean_results.append(v)
            
            logger.info(f"Fetched {len(clean_results)} verses for topic '{topic}'")
            return clean_results
    except Exception as e:
        logger.error(f"Error fetching verses for topic '{topic}': {e}")
        return []

class BiblyAgent:
    def __init__(self, max_days: int = 10):
        self.max_days = max_days
        self.plans = {}  # Store plans by context_id

    def _extract_verse_text(self, verse: dict) -> str:
        """Safely extract verse text from API response"""
        try:
            verses_data = verse.get("verses", {})
            
            # Handle different response formats
            if "kjv" in verses_data:
                kjv = verses_data["kjv"]
            else:
                kjv = verses_data
            
            if isinstance(kjv, dict):
                chapter = next(iter(kjv))
                vnum = next(iter(kjv[chapter]))
                text = kjv[chapter][vnum].get("text", "")
            else:
                text = "Verse text not found."
        except Exception as e:
            logger.warning(f"Error extracting verse text: {e}")
            text = "Verse text not found."
        
        # Sanitize text
        return str(text).strip().replace("\n", " ").replace("\r", " ")

    def _format_verse_reference(self, verse: dict) -> str:
        """Format verse reference like 'John 3:16'"""
        book = verse.get("book_name", "")
        chapter_verse = verse.get("chapter_verse", "")
        return f"{book} {chapter_verse}".strip()

    async def create_plan(
        self,
        topic: str,
        num_days: int,
        context_id: Optional[str] = None,
        start_index: int = 0
    ) -> tuple[TaskResult, str]:
        """Create a new Bible reading plan"""
        num_days = min(num_days, self.max_days)
        verses = await fetch_verses(topic)

        # Fallback verses if API fails
        if not verses:
            logger.warning("No verses found, using fallback")
            verses = [{
                "book_name": "1 Corinthians",
                "chapter_verse": "13:4-7",
                "verses": {
                    "13": {
                        "4": {
                            "text": "Love is patient, love is kind. It does not envy, it does not boast, it is not proud."
                        }
                    }
                }
            }]

        context_id = context_id or str(uuid4())

        # Store plan for continuation
        self.plans[context_id] = {
            "topic": topic,
            "verses": verses,
            "last_index": start_index + num_days - 1,
            "total_days": num_days
        }

        # Build message
        message_lines = []
        artifacts = []
        
        for i in range(num_days):
            idx = start_index + i
            if idx < len(verses):
                verse = verses[idx]
                ref = self._format_verse_reference(verse)
                text = self._extract_verse_text(verse)
                message_lines.append(f"📖 Day {i+1}: {ref}\n   {text}")
                
                # Add artifact for each verse
                artifacts.append(
                    Artifact(
                        name=f"day_{i+1}",
                        parts=[
                            MessagePart(kind="text", text=f"{ref}: {text}")
                        ]
                    )
                )
            else:
                message_lines.append(f"📖 Day {i+1}: No more verses available")

        full_text = (
            f"🕊️ Your {num_days}-Day {topic.title()} Reading Plan\n\n"
            + "\n\n".join(message_lines)
            + f"\n\n💡 To continue, just say 'next {self.max_days} days'"
        )

        # Create response message
        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=full_text)],
            taskId=str(uuid4())
        )

        # Build task result
        task_result = TaskResult(
            id=str(uuid4()),
            contextId=context_id,
            status=TaskStatus(
                state="completed",
                message=response_message
            ),
            artifacts=artifacts,
            history=[response_message]
        )

        return task_result, context_id

    def get_next_chunk(
        self,
        context_id: str,
        num_days: int
    ) -> tuple[Optional[TaskResult], Optional[str]]:
        """Get next chunk of verses for existing plan"""
        entry = self.plans.get(context_id)
        if not entry:
            logger.warning(f"No plan found for context {context_id}")
            return None, None

        num_days = min(num_days, self.max_days)
        start = entry["last_index"] + 1
        verses = entry["verses"]
        topic = entry["topic"]

        # Check if we have more verses
        if start >= len(verses):
            # No more verses available
            response_message = A2AMessage(
                role="agent",
                parts=[
                    MessagePart(
                        kind="text",
                        text=f"🕊️ You've completed all available verses for {topic.title()}!\n\n✨ Start a new plan with a different topic."
                    )
                ]
            )
            
            task_result = TaskResult(
                id=str(uuid4()),
                contextId=context_id,
                status=TaskStatus(state="completed", message=response_message),
                artifacts=[],
                history=[response_message]
            )
            
            return task_result, context_id

        # Build next chunk
        message_lines = []
        artifacts = []
        
        for i in range(num_days):
            idx = start + i
            if idx < len(verses):
                verse = verses[idx]
                ref = self._format_verse_reference(verse)
                text = self._extract_verse_text(verse)
                day_num = entry["total_days"] + i + 1
                message_lines.append(f"📖 Day {day_num}: {ref}\n   {text}")
                
                artifacts.append(
                    Artifact(
                        name=f"day_{day_num}",
                        parts=[MessagePart(kind="text", text=f"{ref}: {text}")]
                    )
                )
            else:
                break

        # Update last index
        entry["last_index"] = start + len(message_lines) - 1
        entry["total_days"] += len(message_lines)

        full_text = (
            f"🕊️ Next {len(message_lines)} Days for {topic.title()}\n\n"
            + "\n\n".join(message_lines)
            + f"\n\n💡 Say 'next {self.max_days} days' to continue"
        )

        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=full_text)]
        )

        task_result = TaskResult(
            id=str(uuid4()),
            contextId=context_id,
            status=TaskStatus(state="completed", message=response_message),
            artifacts=artifacts,
            history=[response_message]
        )

        return task_result, context_id

    def clear_plan(self, context_id: str):
        """Clear a specific plan"""
        if context_id in self.plans:
            del self.plans[context_id]
            logger.info(f"Cleared plan for context {context_id}")