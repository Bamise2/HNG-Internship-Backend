import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models.a2a import (
    JSONRPCRequest, 
    MessageParams, 
    ExecuteParams, 
    A2AMessage,
    TaskResult,
    TaskStatus,
    MessagePart
)
from agents.bibly_agent import BiblyAgent
from pydantic import ValidationError
from uuid import uuid4

app = FastAPI(title="Bibly A2A Agent")

# Instantiate agent
agent = BiblyAgent(max_days=10)
user_contexts = {}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "bibly"}

@app.get("/a2a/metadata")
def metadata():
    return {
        "schema_version": "2.0",
        "name": "ScriptureStream",
        "short_description": "Generates Bible reading plans by topic and duration.",
        "description": "An AI agent that creates themed, multi-day Bible reading plans based on any topic. Say 'create a 7 day plan about faith' or 'next 10 days'.",
        "type": "a2a",
        "version": "1.0.0",
        "inputs": {"input_text": {"type": "string", "description": "User text input"}},
        "author": "Shogbesan Oluwabamiseyori",
        "email": "shogbesanoluwabamiseyori@gmail.com"
    }

async def handle_a2a_request(request: Request):
    """Shared handler for A2A requests"""
    try:
        body = await request.json()

        # Validate JSON-RPC structure
        if body.get("jsonrpc") != "2.0" or "id" not in body:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required"
                    }
                }
            )

        # Validate the JSON-RPC request
        try:
            rpc = JSONRPCRequest(**body)
        except ValidationError as ve:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": {"details": str(ve)}
                    }
                }
            )

        # Extract messages and context
        messages = []
        context_id = None
        task_id = None

        if rpc.method == "message/send":
            messages = [rpc.params.message]
            task_id = rpc.params.message.taskId
        elif rpc.method == "execute":
            messages = rpc.params.messages
            context_id = rpc.params.contextId
            task_id = rpc.params.taskId
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": rpc.id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
            )

        # Extract user input text
        text = ""
        if messages:
            last_message = messages[-1]
            for part in last_message.parts:
                if part.kind == "text" and part.text:
                    text += part.text.strip() + " "
            text = text.strip()

        if not text:
            text = "faith"  # Default topic

        # Generate IDs if not provided
        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())

        # Check for "next X days" pattern
        next_match = re.search(r"next\s+(\d+)\s*[-]?\s*day(?:s)?", text, re.I)
        if next_match and context_id in user_contexts:
            # Continue existing plan
            num = min(int(next_match.group(1)), agent.max_days)
            task_result, _ = agent.get_next_chunk(context_id, num)
            
            if task_result is None:
                # No existing plan found
                return JSONResponse(
                    status_code=200,
                    content={
                        "jsonrpc": "2.0",
                        "id": rpc.id,
                        "result": {
                            "id": task_id,
                            "contextId": context_id,
                            "status": {
                                "state": "completed",
                                "timestamp": TaskStatus().timestamp,
                                "message": {
                                    "messageId": str(uuid4()),
                                    "role": "agent",
                                    "parts": [
                                        {
                                            "kind": "text",
                                            "text": "I couldn't find an existing reading plan. Please create a new plan first, e.g., 'Create a 7-day plan about faith'."
                                        }
                                    ],
                                    "kind": "message",
                                    "taskId": task_id
                                }
                            },
                            "artifacts": [],
                            "history": messages + [{
                                "messageId": str(uuid4()),
                                "role": "agent",
                                "parts": [{"kind": "text", "text": "No existing plan found."}],
                                "kind": "message",
                                "taskId": task_id
                            }],
                            "kind": "task"
                        }
                    }
                )
        else:
            # Create new plan
            # Parse topic and number of days
            create_match = re.search(r"(\d+)\s*[-]?\s*day(?:s)?\b.*\b(?:on|about|for)\b\s+(.+)", text, re.I)
            if create_match:
                num = min(int(create_match.group(1)), agent.max_days)
                topic = create_match.group(2).strip()
            else:
                topic_match = re.search(r"(?:about|on|for)\s+(.+)", text, re.I)
                if topic_match:
                    topic = topic_match.group(1).strip()
                    num = 5
                else:
                    topic = text or "faith"
                    num = 5

            # Create the plan
            task_result, ctx = await agent.create_plan(topic, num, context_id)
            user_contexts[context_id] = ctx

        # Update IDs to match request
        task_result.id = task_id
        task_result.contextId = context_id

        # Update history with original messages
        task_result.history = messages + [task_result.status.message]

        # Return proper JSON-RPC response
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": rpc.id,
                "result": task_result.model_dump()
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            }
        )


@app.post("/a2a/scripture")
async def a2a_scripture(request: Request):
    """Main A2A endpoint - matches the URL in a2a.json"""
    return await handle_a2a_request(request)


@app.post("/a2a/execute")
async def a2a_execute(request: Request):
    """Alternative endpoint for backward compatibility"""
    return await handle_a2a_request(request)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)