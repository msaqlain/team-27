from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.workflow_manager import workflow_manager

router = APIRouter()

class TextInput(BaseModel):
    text: str

@router.post("/process")
async def process_text(input_data: TextInput):
    """Process text through the workflow"""
    try:
        result = await workflow_manager.process_input(input_data.text)
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