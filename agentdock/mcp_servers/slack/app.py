from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx

app = FastAPI(title="Slack MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SlackConfig(BaseModel):
    token: str

class SlackMessage(BaseModel):
    channel: str
    text: str

class SlackChannel(BaseModel):
    id: str
    name: str

# State
slack_token: Optional[str] = None

@app.post("/configure")
async def configure_slack(config: SlackConfig):
    """Configure Slack connection with token"""
    global slack_token
    slack_token = config.token
    return {"status": "success", "message": "Slack token configured"}

@app.get("/config")
async def get_config():
    """Get current Slack token configuration"""
    if not slack_token:
        raise HTTPException(status_code=404, detail="Slack not configured")
    return {"token": slack_token}

@app.post("/deregister")
async def deregister():
    """Deregister the Slack agent"""
    global slack_token
    slack_token = None
    return {"status": "success", "message": "Slack agent deregistered"}

@app.get("/channels")
async def list_channels():
    """List all Slack channels"""
    if not slack_token:
        raise HTTPException(status_code=400, detail="Slack not configured")

    headers = {
        "Authorization": f"Bearer {slack_token}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.list",
            headers=headers
        )

        data = response.json()
        if not data.get("ok"):
            raise HTTPException(status_code=400, detail="Failed to list channels")

        return [{"id": ch["id"], "name": ch["name"]} for ch in data["channels"]]

@app.post("/message")
async def send_message(payload: SlackMessage):
    """Send a message to a Slack channel"""
    if not slack_token:
        raise HTTPException(status_code=400, detail="Slack not configured")

    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json={
                "channel": payload.channel,
                "text": payload.text
            }
        )

        data = response.json()
        if not data.get("ok"):
            raise HTTPException(status_code=400, detail="Failed to send message")

        return {"status": "success", "message": "Message sent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
