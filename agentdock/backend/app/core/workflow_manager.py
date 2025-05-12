from typing import Dict, List, Optional
import httpx
import asyncio
from app.core.config import settings
from app.workflows.langchain_service import LangChainService

class WorkflowManager:
    def __init__(self):
        self.supervisor_url = "http://localhost:8005"
        self.services: Dict[str, LangChainService] = {}
        self.context: Dict = {}
        self.is_running = False

    async def initialize_services(self):
        """Initialize all services and register them with supervisor"""
        # Create services
        self.services = {
            "text-processor": LangChainService(
                service_id="text-processor",
                name="Text Processing Service",
                prompt_template="Process the following text: {text}\nAnalysis:",
                input_variables=["text"]
            ),
            "sentiment-analyzer": LangChainService(
                service_id="sentiment-analyzer",
                name="Sentiment Analysis Service",
                prompt_template="Analyze the sentiment of: {text}\nSentiment:",
                input_variables=["text"]
            ),
            "response-generator": LangChainService(
                service_id="response-generator",
                name="Response Generation Service",
                prompt_template="Generate a response based on: {text}\nResponse:",
                input_variables=["text"]
            )
        }

        # Register services with supervisor
        async with httpx.AsyncClient() as client:
            for service in self.services.values():
                await service.register()

        # Set execution order
        await self.set_execution_order([
            "text-processor",
            "sentiment-analyzer",
            "response-generator"
        ])

    async def set_execution_order(self, order: List[str]):
        """Set the execution order in the supervisor"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supervisor_url}/set-order",
                json=order
            )
            response.raise_for_status()

    async def process_input(self, input_text: str) -> Dict:
        """Process input through the workflow"""
        self.context = {"text": input_text}
        
        # Start all services
        tasks = []
        for service in self.services.values():
            tasks.append(asyncio.create_task(service.run(self.context)))
        
        # Wait for all services to complete
        await asyncio.gather(*tasks)
        
        return self.context

    async def get_status(self) -> Dict:
        """Get current workflow status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.supervisor_url}/status")
            return response.json()

    def stop(self):
        """Stop all services"""
        for service in self.services.values():
            service.stop()

# Create global workflow manager instance
workflow_manager = WorkflowManager() 