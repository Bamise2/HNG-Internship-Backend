Bibly: Personalized Bible Reading Agent

Bibly is a spiritual growth assistant that generates multi-day, themed Bible reading plans. Built with Python and FastAPI, Bibly leverages the A2A protocol to deliver structured scripture plans directly via Telex.

Features

Generate 5–10 day Bible reading plans on topics like love, faith, hope, and peace.

Fetches scripture verses dynamically from Bible SuperSearch API.

Supports continuation: retrieve the next set of readings from an ongoing plan.

Fully compliant with Telex A2A messaging and task result standards.

In-memory context storage allows for personalized, multi-step plans.

Installation

Clone the repository:

git clone https://github.com/yourusername/bibly.git
cd bibly


Create a virtual environment and install dependencies:

python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt

Configuration

No extra configuration is needed for local testing.

Port: The app defaults to 8000 or you can set it via the PORT environment variable.

Max Days: You can configure the maximum number of days in agents/bibly_agent.py (max_days parameter).

Running the Agent

Start the FastAPI server:

uvicorn main:app --host 0.0.0.0 --port 8000 --reload


Endpoints:

Endpoint	Method	Description
/a2a/metadata	GET	Returns agent metadata and inputs configuration.
/a2a/scripture	POST	Accepts A2A JSON-RPC requests (message/send or execute) and returns a TaskResult.
Usage Example

Request (message/send):

{
  "jsonrpc": "2.0",
  "id": "example-1",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Create a 7-day plan about love"}]
    }
  }
}


Response (TaskResult):

{
  "jsonrpc": "2.0",
  "id": "example-1",
  "result": {
    "id": "f26a7d72-05f6-4cf5-9745-3cd8b6518a68",
    "contextId": "fab4b4da-e07a-4041-8b18-8f7dfef85d46",
    "status": {
      "state": "completed",
      "message": {
        "role": "agent",
        "parts": [
          {
            "kind": "text",
            "text": "Your 7-Day Love Reading Plan: ..."
          }
        ]
      }
    },
    "artifacts": [],
    "history": [],
    "kind": "task"
  }
}

Challenges & Notes

Verse retrieval: Handling the Bible API responses and mapping them to the plan.

Plan continuation: Managing in-memory context for users.

A2A compliance: Ensuring all responses match the Telex JSON-RPC and TaskResult format.

Error handling: Providing meaningful JSON-RPC errors when requests are invalid or context is missing.