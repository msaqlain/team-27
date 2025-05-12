from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.workflow_manager import workflow_manager

router = APIRouter()

class TextInput(BaseModel):
    text: str
    github_data: Optional[Dict[str, Any]] = None
    slack_data: Optional[Dict[str, Any]] = None
    jira_data: Optional[Dict[str, Any]] = None

@router.post("/process")
async def process_text(input_data: TextInput):
    """Process text through the workflow"""
    try:
        # Combine all integration data
        integration_data = {}
        if input_data.github_data:
            integration_data.update(input_data.github_data)
        if input_data.slack_data:
            integration_data.update(input_data.slack_data)
        if input_data.jira_data:
            integration_data.update(input_data.jira_data)

        result = await workflow_manager.process_input(
            input_text=input_data.text,
            integration_data=integration_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_workflow_status():
    """Get current workflow status"""
    try:
        status = await workflow_manager.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_workflow():
    """Initialize the workflow and its services"""
    try:
        await workflow_manager.initialize_services()
        return {"message": "Workflow initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 