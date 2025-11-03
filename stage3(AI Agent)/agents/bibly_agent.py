# agents/bibly_agent.py
from typing import Optional
from models.a2a import A2AMessage, MessagePart, TaskResult, TaskStatus
from uuid import uuid4
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_verses(topic: str) -> list:
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
            return clean_results
    except Exception as e:
        logger.error(f"Error fetching verses for topic '{topic}': {e}")
        return []

class BiblyAgent:
    def __init__(self, max_days: int = 10):
        self.max_days = max_days
        self.plans = {}

    async def create_plan(self, topic: str, num_days: int, context_id: Optional[str] = None, start_index: int = 0):
        num_days = min(num_days, self.max_days)
        verses = await fetch_verses(topic)

        # fallback verses
        if not verses:
            verses = [{
                "book_name": "1 Corinthians",
                "chapter_verse": "13:4-7",
                "verses": {"13": {"4": {"text": "Love is patient, love is kind; it does not envy or boast."}}}
            }]

        context_id = context_id or str(uuid4())

        self.plans[context_id] = {
            "topic": topic,
            "verses": verses,
            "last_index": start_index + num_days - 1
        }

        message_lines = []
        for i in range(num_days):
            idx = start_index + i
            if idx < len(verses):
                verse = verses[idx]
                book = verse.get("book_name", "")
                chapter_verse = verse.get("chapter_verse", "")
                try:
                    kjv = verse.get("verses", {}).get("kjv", {})
                    if isinstance(kjv, dict):
                        chapter = next(iter(kjv))
                        vnum = next(iter(kjv[chapter]))
                        text = kjv[chapter][vnum]["text"]
                    else:
                        text = "Verse text not found."
                except Exception:
                    text = "Verse text not found."
                # sanitize weird endings
                safe_text = str(text).strip().replace("\n", " ").replace("\r", " ")
                ref = f"{book} {chapter_verse}".strip()
                message_lines.append(f"📖 Day {i+1}: {ref} — {safe_text}")
            else:
                message_lines.append(f"📖 Day {i+1}: No verse found for this day.")

        full_text = f"🕊️ Your {num_days}-Day {topic.title()} Reading Plan\n\n" + "\n\n".join(message_lines)

        status = TaskStatus(
            state="completed",
            message=A2AMessage(
                role="agent",
                parts=[MessagePart(kind="text", text=full_text)]
            )
        )

        task_result = TaskResult(
            id=str(uuid4()),
            contextId=context_id,
            status=status,
            artifacts=[],
            history=[]
        )

        return task_result, context_id

    def get_next_chunk(self, context_id: str, num_days: int):
        entry = self.plans.get(context_id)
        if not entry:
            return None, None

        start = entry["last_index"] + 1
        verses = entry["verses"]
        topic = entry["topic"]

        message_lines = []
        for i in range(num_days):
            idx = start + i
            if idx < len(verses):
                verse = verses[idx]
                book = verse.get("book_name", "")
                chapter_verse = verse.get("chapter_verse", "")
                try:
                    kjv = verse.get("verses", {}).get("kjv", {})
                    if isinstance(kjv, dict):
                        chapter = next(iter(kjv))
                        vnum = next(iter(kjv[chapter]))
                        text = kjv[chapter][vnum]["text"]
                    else:
                        text = "Verse text not found."
                except Exception:
                    text = "Verse text not found."

                safe_text = str(text).strip().replace("\n", " ").replace("\r", " ")
                ref = f"{book} {chapter_verse}".strip()
                message_lines.append(f"📖 Day {idx+1}: {ref} — {safe_text}")
            else:
                message_lines.append(f"📖 Day {idx+1}: No verse found for this day.")

        entry["last_index"] = start + num_days - 1
        full_text = f"🕊️ Next {num_days} Days for {topic.title()}\n\n" + "\n\n".join(message_lines)

        status = TaskStatus(
            state="completed",
            message=A2AMessage(role="agent", parts=[MessagePart(kind="text", text=full_text)])
        )

        task_result = TaskResult(
            id=str(uuid4()),
            contextId=context_id,
            status=status,
            artifacts=[],
            history=[]
        )

        return task_result, context_id
