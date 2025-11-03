# main.py
import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models.a2a import JSONRPCRequest, MessageParams, ExecuteParams, TaskResult, A2AMessage, MessagePart

from agents.bibly_agent import BiblyAgent
from pydantic import ValidationError

app = FastAPI(title="Bibly A2A Agent")

# instantiate agent
agent = BiblyAgent(max_days=10)

# in-memory mapping from user_id -> context_id (optional helper)
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
    """
    Accepts JSON-RPC 2.0 A2A requests with method "message/send" or "execute".
    Returns JSON-RPC 2.0 responses with a TaskResult in `result`.
    """
    body = await request.json()
    # Validate basic JSON-RPC shape using Pydantic model
    try:
        rpc = JSONRPCRequest(**body)
    except ValidationError as ve:
        # return JSON-RPC error format
        return JSONResponse(status_code=400, content={
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "error": {"code": -32600, "message": "Invalid Request", "data": str(ve)}
        })

    # extract user id if present in metadata (Telex often includes context)
    user_id = None
    # Try to find a user id in params/message metadata if provided
    try:
        if isinstance(rpc.params, MessageParams):
            user_id = rpc.params.message.metadata.get("user_id") if rpc.params.message.metadata else None
    except Exception:
        user_id = None

    # If this is a message/send (single message)
    if rpc.method == "message/send":
        message: A2AMessage = rpc.params.message
        # get the text from the first text part
        text = ""
        for p in message.parts:
            if p.kind == "text" and p.text:
                text = p.text.strip()
                break

        # If user asks for "next X days"
        next_match = re.search(r"next\s+(\d+)\s*days?", text, re.I)
        if next_match and user_id:
            num = min(int(next_match.group(1)), agent.max_days)
            # lookup context for user
            context_id = user_contexts.get(user_id)
            if not context_id:
                # no context - return error result
                return JSONResponse(status_code=200, content={
                    "jsonrpc": "2.0",
                    "id": rpc.id,
                    "result": None,
                    "error": {"code": -32000, "message": "No existing plan found. Create a plan first."}
                })
            task_result, ctx = agent.get_next_chunk(context_id, num)
            return JSONResponse(status_code=200, content={
                "jsonrpc": "2.0",
                "id": rpc.id,
                "result": task_result.model_dump()
            })

        # Otherwise parse "create X day plan about Y"
        create_match = re.search(r"(\d+)\s*[-]?\s*day(?:s)?\b.*\b(?:on|about)\b\s+(.+)", text, re.I)
        if create_match:
            num = min(int(create_match.group(1)), agent.max_days)
            topic = create_match.group(2).strip()
        else:
            # fallback: try "create a plan about X" or assume entire text is topic
            topic_match = re.search(r"(?:about|on)\s+(.+)", text, re.I)
            if topic_match:
                topic = topic_match.group(1).strip()
                num = 5
            else:
                # If the text starts with a number, use it
                days_match = re.search(r"^(\d+)\b", text)
                if days_match:
                    num = min(int(days_match.group(1)), agent.max_days)
                    # remove leading number and use rest as topic
                    topic = text[days_match.end():].strip() or "faith"
                else:
                    # default
                    topic = text or "faith"
                    num = 5

        # create plan
        task_result, ctx = await agent.create_plan(topic, num)
        # store mapping for user if provided
        if user_id:
            user_contexts[user_id] = ctx

        return JSONResponse(status_code=200, content={
            "jsonrpc": "2.0",
            "id": rpc.id,
            "result": task_result.model_dump()
        })

    # If method is execute (batch messages)
    elif rpc.method == "execute":
        # Extract messages
        msgs = rpc.params.messages if hasattr(rpc.params, "messages") else []
        if not msgs:
            return JSONResponse(status_code=400, content={
                "jsonrpc": "2.0",
                "id": rpc.id,
                "error": {"code": -32602, "message": "No messages provided"}
            })

        # For simplicity, take last message as instruction
        last_msg = msgs[-1]
        # combine text parts
        text = ""
        for p in last_msg.parts:
            if p.kind == "text" and p.text:
                text += p.text.strip() + " "

        text = text.strip()
        # Same parsing logic as above
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

        task_result, ctx = await agent.create_plan(topic, num)
        # try to store context if message had metadata containing user_id
        try:
            uid = last_msg.metadata.get("user_id") if last_msg.metadata else None
            if uid:
                user_contexts[uid] = ctx
        except Exception:
            pass

        return JSONResponse(status_code=200, content={
            "jsonrpc": "2.0",
            "id": rpc.id,
            "result": task_result.model_dump()
        })

    # Unrecognized method
    return JSONResponse(status_code=400, content={
        "jsonrpc": "2.0",
        "id": rpc.id,
        "error": {"code": -32601, "message": "Method not found"}
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
