from typing import List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from dapr.clients import DaprClient
import json
import logging

app = FastAPI(title="Supervisor Node")

class ServiceNode(BaseModel):
    service_id: str
    name: str
    status: str = "pending"
    order: int = 0

class ExecutionOrder(BaseModel):
    order: List[str]  # List of service_ids in execution order
    current_index: int = 0

# In-memory storage for service nodes and execution order
service_nodes: Dict[str, ServiceNode] = {}
execution_order = ExecutionOrder(order=[])

@app.post("/register")
async def register_service(service: ServiceNode):
    """Register a new service node"""
    service_nodes[service.service_id] = service
    return {"message": f"Service {service.name} registered successfully"}

@app.post("/set-order")
async def set_execution_order(order: List[str]):
    """Set the execution order for services"""
    # Validate that all services in order exist
    for service_id in order:
        if service_id not in service_nodes:
            raise HTTPException(status_code=400, detail=f"Service {service_id} not registered")
    
    execution_order.order = order
    execution_order.current_index = 0
    return {"message": "Execution order set successfully"}

@app.get("/next-service")
async def get_next_service():
    """Get the next service to execute"""
    if execution_order.current_index >= len(execution_order.order):
        return {"message": "All services completed"}
    
    next_service_id = execution_order.order[execution_order.current_index]
    return {
        "service_id": next_service_id,
        "service_name": service_nodes[next_service_id].name
    }

@app.post("/complete/{service_id}")
async def mark_service_complete(service_id: str):
    """Mark a service as completed and move to next service"""
    if service_id not in service_nodes:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if service_id != execution_order.order[execution_order.current_index]:
        raise HTTPException(status_code=400, detail="Not this service's turn")
    
    service_nodes[service_id].status = "completed"
    execution_order.current_index += 1
    
    return {"message": f"Service {service_id} marked as completed"}

@app.get("/status")
async def get_status():
    """Get current execution status"""
    return {
        "execution_order": execution_order.order,
        "current_index": execution_order.current_index,
        "services": {k: v.dict() for k, v in service_nodes.items()}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 