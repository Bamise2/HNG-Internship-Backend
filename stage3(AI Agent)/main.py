from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import re
import asyncio
import os
import uvicorn

app = FastAPI()

MAX_DAYS = 10  # Cap the number of days to prevent huge messages

# --- Helper function to fetch verses ---
async def fetch_verses(client: httpx.AsyncClient, topic: str) -> list:
    """
    Fetches verses from Bible SuperSearch API with whole-word match.
    """
    api_url = f"https://api.biblesupersearch.com/api?bible=kjv&search={topic}&whole_word=on"
    
    try:
        response = await client.get(api_url, timeout=10.0)
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []

        data = response.json()
        return data.get("results", [])
        
    except Exception as e:
        print(f"Error fetching verses: {e}")
        return []


# --- A2A Metadata Endpoint ---
@app.get("/a2a/metadata")
def metadata():
    return {
        "schema_version": "v1",
        "name": "Bibly",
        "description": "An AI agent that creates themed, multi-day Bible reading plans based on any topic.",
        "short_description": "Generates Bible reading plans by topic and duration.",
        "type": "a2a",
        "version": "1.0.0",
        "inputs": {
            "input_text": {
                "type": "string",
                "description": "User's request, e.g., 'Create a 7-day plan on faith'"
            }
        },
        "author": "Shogbesan Oluwabamiseyori",
        "email": "shogbesanoluwabamiseyori@gmail.com"
    }


# --- A2A Execute Endpoint ---
@app.post("/a2a/execute")
async def execute(request: Request):
    body = await request.json()
    input_text = body.get("input_text", "").strip()

    if not input_text:
        return JSONResponse({
            "event_name": "message",
            "data": {"text": "Please provide a topic to create a reading plan."}
        })

    # --- Extract Topic ---
    match = re.search(r"about\s+([\w\s']+)", input_text.lower())
    topic = match.group(1).strip() if match else input_text

    # --- Extract Number of Days (default 5, capped at MAX_DAYS) ---
    days_match = re.search(r"(\d+)[-\s]?day", input_text.lower())
    num_days = min(int(days_match.group(1)) if days_match else 5, MAX_DAYS)

    # --- Send "working..." message ---
    intro_message = {
        "event_name": "message",
        "data": {"text": f"Creating your {num_days}-day reading plan on {topic}!"}
    }

    async with httpx.AsyncClient() as client:
        verses = await fetch_verses(client, topic)

    if not verses:
        return JSONResponse({
            "event_name": "message",
            "data": {"text": f"Sorry, I couldn't find any verses with the word '{topic}'."}
        })

    # --- Build the reading plan ---
    message_lines = []
    for i in range(num_days):
        if i < len(verses):
            verse = verses[i]
            book = verse.get("book_name", "")
            chapter_verse = verse.get("chapter_verse", "")
            text = ""

            try:
                kjv_section = verse.get("verses", {}).get("kjv", {})
                chapter = list(kjv_section.keys())[0]
                verse_num = list(kjv_section[chapter].keys())[0]
                text = kjv_section[chapter][verse_num]["text"]
            except Exception:
                text = "Verse text not found."

            ref = f"{book} {chapter_verse}".strip()
            message_lines.append(f"📖 Day {i+1}: {ref} — {text}")
        else:
            message_lines.append(f"📖 Day {i+1}: No verse found for this day.")

    # --- Compose final message ---
    message = f"🕊️ Your {num_days}-Day {topic.title()} Reading Plan\n\n" + "\n\n".join(message_lines)

    # --- Return both intro and result events ---
    return JSONResponse({
        "events": [
            intro_message,
            {"event_name": "message", "data": {"text": message}}
        ]
    })


# --- Run app locally or on Railway ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
