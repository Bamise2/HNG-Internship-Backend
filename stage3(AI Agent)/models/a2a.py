# models/a2a.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import uuid4

def gen_id():
    return str(uuid4())

class MessagePart(BaseModel):
    kind: Literal["text", "file", "data"] = "text"
    text: Optional[str] = None
    data: Optional[Union[Dict[str, Any], List[Any]]] = None  # ✅ Accept both dict and list
    file_url: Optional[str] = None
    
    @field_validator('data', mode='before')
    @classmethod
    def validate_data(cls, v):
        """Accept both dict and list for data field"""
        if v is None:
            return None
        # If it's already a dict or list, return as is
        if isinstance(v, (dict, list)):
            return v
        # Try to parse if it's a string
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                return v
        return v

class A2AMessage(BaseModel):
    kind: Literal["message"] = "message"
    role: Literal["user", "agent", "system"] = "user"
    parts: List[MessagePart] = []
    messageId: str = Field(default_factory=gen_id)
    taskId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PushNotificationConfig(BaseModel):
    url: str
    token: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None

class MessageConfiguration(BaseModel):
    blocking: bool = True
    acceptedOutputModes: List[str] = ["text/plain", "image/png", "image/svg+xml"]
    pushNotificationConfig: Optional[PushNotificationConfig] = None
    historyLength: Optional[int] = None  # ✅ Add this field

class MessageParams(BaseModel):
    message: A2AMessage
    configuration: MessageConfiguration = Field(default_factory=MessageConfiguration)

class ExecuteParams(BaseModel):
    contextId: Optional[str] = None
    taskId: Optional[str] = None
    messages: List[A2AMessage]

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: str
    method: Literal["message/send", "execute"]
    params: Union[MessageParams, ExecuteParams]
    
    @field_validator('params', mode='before')
    @classmethod
    def validate_params(cls, v, info):
        """Validate params based on method"""
        if not isinstance(v, dict):
            return v
        
        # If it has 'message' key, it's MessageParams
        if 'message' in v:
            return v
        
        # If it has 'messages' key, it's ExecuteParams
        if 'messages' in v:
            return v
        
        # Default to MessageParams for backward compatibility
        return v

class TaskStatus(BaseModel):
    state: Literal["working", "completed", "input-required", "failed"] = "working"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    message: Optional[A2AMessage] = None

class Artifact(BaseModel):
    artifactId: str = Field(default_factory=gen_id)
    name: str
    parts: List[MessagePart] = []

class TaskResult(BaseModel):
    id: str
    contextId: str
    status: TaskStatus
    artifacts: List[Artifact] = []
    history: List[A2AMessage] = []
    kind: Literal["task"] = "task"