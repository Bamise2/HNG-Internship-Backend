# agents/bibly_agent.py
from typing import Optional, List
from models.a2a import A2AMessage, MessagePart, TaskResult, TaskStatus, Artifact
from uuid import uuid4
import httpx
import asyncio

async def fetch_verses(topic: str) -> list:
    api_url = f"https://api.biblesupersearch.com/api?bible=kjv&search={topic}&whole_word=on"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=10.0)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data.get("results", [])
    except Exception:
        return []

class BiblyAgent:
    def __init__(self, max_days: int = 10):
        self.max_days = max_days
        # in-memory store of plans per context / user (contextId -> plan dict)
        self.plans = {}

    async def create_plan(self, topic: str, num_days: int, context_id: Optional[str] = None, start_index: int = 0):
        """
        Fetch verses, slice for num_days starting at start_index, and build TaskResult-like dict.
        Returns (task_result_dict, new_context_id)
        """
        num_days = min(num_days, self.max_days)
        verses = await fetch_verses(topic)
        # create context id if not provided
        context_id = context_id or str(uuid4())

        # save full verses into plan store for continuation
        self.plans[context_id] = {
            "topic": topic,
            "verses": verses,
            "last_index": start_index + num_days - 1
        }

        # build message text
        message_lines = []
        for i in range(num_days):
            idx = start_index + i
            if idx < len(verses):
                verse = verses[idx]
                book = verse.get("book_name", "")
                chapter_verse = verse.get("chapter_verse", "")
                text = ""
                try:
                    kjv = verse.get("verses", {}).get("kjv", {})
                    chapter = list(kjv.keys())[0]
                    vnum = list(kjv[chapter].keys())[0]
                    text = kjv[chapter][vnum]["text"]
                except Exception:
                    text = "Verse text not found."
                ref = f"{book} {chapter_verse}".strip()
                message_lines.append(f"📖 Day {start_index + i + 1}: {ref} — {text}")
            else:
                message_lines.append(f"📖 Day {start_index + i + 1}: No verse found for this day.")

        full_text = f"🕊️ Your {num_days}-Day {topic.title()} Reading Plan\n\n" + "\n\n".join(message_lines)

        # Build A2A models as dicts (TaskResult compatible)
        status = TaskStatus(state="completed", message=A2AMessage(role="agent", parts=[MessagePart(kind="text", text=full_text)]))
        artifacts = []
        history = []

        task_result = TaskResult(
            id=str(uuid4()),
            contextId=context_id,
            status=status,
            artifacts=artifacts,
            history=history
        )

        return task_result, context_id

    def get_next_chunk(self, context_id: str, num_days: int):
        """
        Return the next num_days from stored plan, update last_index.
        """
        entry = self.plans.get(context_id)
        if not entry:
            return None, None
        start = entry["last_index"] + 1
        verses = entry["verses"]
        topic = entry["topic"]
        # build chunk
        message_lines = []
        for i in range(num_days):
            idx = start + i
            if idx < len(verses):
                verse = verses[idx]
                book = verse.get("book_name", "")
                chapter_verse = verse.get("chapter_verse", "")
                text = ""
                try:
                    kjv = verse.get("verses", {}).get("kjv", {})
                    chapter = list(kjv.keys())[0]
                    vnum = list(kjv[chapter].keys())[0]
                    text = kjv[chapter][vnum]["text"]
                except Exception:
                    text = "Verse text not found."
                ref = f"{book} {chapter_verse}".strip()
                message_lines.append(f"📖 Day {idx+1}: {ref} — {text}")
            else:
                message_lines.append(f"📖 Day {idx+1}: No verse found for this day.")
        entry["last_index"] = start + num_days - 1
        full_text = f"🕊️ Next {num_days} Days for {topic.title()}\n\n" + "\n\n".join(message_lines)
        status = TaskStatus(state="completed", message=A2AMessage(role="agent", parts=[MessagePart(kind="text", text=full_text)]))
        task_result = TaskResult(
            id=str(uuid4()),
            contextId=context_id,
            status=status,
            artifacts=[],
            history=[]
        )
        return task_result, context_id
