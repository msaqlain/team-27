from typing import Optional, Dict, Any
import httpx
import asyncio
import logging
from pydantic import BaseModel

class ServiceNode:
    def __init__(
        self,
        service_id: str,
        name: str,
        supervisor_url: str = "http://localhost:8005",
        check_interval: int = 5
    ):
        self.service_id = service_id
        self.name = name
        self.supervisor_url = supervisor_url
        self.check_interval = check_interval
        self.logger = logging.getLogger(name)
        self.is_running = False

    async def register(self):
        """Register this service with the supervisor"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supervisor_url}/register",
                json={"service_id": self.service_id, "name": self.name}
            )
            response.raise_for_status()
            self.logger.info(f"Registered with supervisor: {response.json()}")

    async def check_turn(self) -> bool:
        """Check if it's this service's turn to run"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.supervisor_url}/next-service")
            if response.status_code == 200:
                data = response.json()
                if "service_id" in data and data["service_id"] == self.service_id:
                    return True
        return False

    async def mark_complete(self):
        """Mark this service as completed"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supervisor_url}/complete/{self.service_id}"
            )
            response.raise_for_status()
            self.logger.info(f"Marked as complete: {response.json()}")

    async def execute(self, context: Optional[Dict[str, Any]] = None):
        """Execute the service's main logic. Override this in subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")

    async def run(self, context: Optional[Dict[str, Any]] = None):
        """Main run loop for the service"""
        self.is_running = True
        await self.register()

        while self.is_running:
            try:
                if await self.check_turn():
                    self.logger.info(f"Starting execution of {self.name}")
                    await self.execute(context)
                    await self.mark_complete()
                    self.logger.info(f"Completed execution of {self.name}")
                else:
                    self.logger.debug("Not my turn yet")
                
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in service {self.name}: {str(e)}")
                await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the service"""
        self.is_running = False 