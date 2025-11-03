import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models.a2a import JSONRPCRequest, MessageParams, ExecuteParams, A2AMessage
from agents.bibly_agent import BiblyAgent
from pydantic import ValidationError

app = FastAPI(title="Bibly A2A Agent")

# instantiate agent
agent = BiblyAgent(max_days=10)
user_contexts = {}

@app.get("/a2a/metadata")
def metadata():
    return {
        "schema_version": "2.0",
        "name": "Bibly",
        "short_description": "Generates Bible reading plans by topic and duration.",
        "description": "An AI agent that creates themed, multi-day Bible reading plans based on any topic. Say 'create a 7 day plan about faith' or 'next 10 days'.",
        "type": "a2a",
        "version": "1.0.0",
        "inputs": {"input_text": {"type": "string", "description": "User text input"}},
        "author": "Shogbesan Oluwabamiseyori",
        "email": "shogbesanoluwabamiseyori@gmail.com"
    }

@app.post("/a2a/scripture")
async def a2a_scripture(request: Request):
    body = await request.json()

    # ✅ Validate the JSON-RPC request
    try:
        rpc = JSONRPCRequest(**body)
    except ValidationError as ve:
        return JSONResponse(status_code=400, content={
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "error": {"code": -32600, "message": "Invalid Request", "data": str(ve)}
        })

    # ✅ Extract user input text
    text = ""
    if rpc.method == "message/send":
        for part in rpc.params.message.parts:
            if part.kind == "text" and part.text:
                text = part.text.strip()
                break
    elif rpc.method == "execute":
        messages = rpc.params.messages if hasattr(rpc.params, "messages") else []
        if messages:
            last = messages[-1]
            for part in last.parts:
                if part.kind == "text" and part.text:
                    text += part.text.strip() + " "
            text = text.strip()
    else:
        return JSONResponse(status_code=400, content={
            "jsonrpc": "2.0",
            "id": rpc.id,
            "error": {"code": -32601, "message": "Method not found"}
        })

    # ✅ Parse topic and number of days
    create_match = re.search(r"(\d+)\s*[-]?\s*day(?:s)?\b.*\b(?:on|about)\b\s+(.+)", text, re.I)
    if create_match:
        num = min(int(create_match.group(1)), agent.max_days)
        topic = create_match.group(2).strip()
    else:
        topic_match = re.search(r"(?:about|on)\s+(.+)", text, re.I)
        if topic_match:
            topic = topic_match.group(1).strip()
            num = 5
        else:
            topic = text or "faith"
            num = 5

    # ✅ Create the plan
    task_result, ctx = await agent.create_plan(topic, num)

    # ✅ Extract plain text for Telex
    try:
        plan_text = task_result.status.message.parts[0].text
    except Exception:
        plan_text = "Sorry, I couldn't generate your reading plan."

    # ✅ Return in Telex-compatible format
    return JSONResponse(status_code=200, content={
        "jsonrpc": "2.0",
        "id": rpc.id,
        "result": {
            "messages": [
                {
                    "role": "assistant",
                    "parts": [
                        {"kind": "text", "text": plan_text}
                    ]
                }
            ]
        }
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
