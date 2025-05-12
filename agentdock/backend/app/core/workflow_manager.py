from typing import Dict, List, Optional
import httpx
import asyncio
from app.core.config import settings

class WorkflowManager:
    def __init__(self):
        self.supervisor_url = "http://localhost:8005"
        self.context: Dict = {}
        self.is_running = False
        # MCP server URLs
        self.github_mcp_url = f"http://localhost:{settings.GITHUB_MCP_PORT}"
        self.slack_mcp_url = f"http://localhost:{settings.SLACK_MCP_PORT}"
        self.jira_mcp_url = f"http://localhost:{settings.JIRA_MCP_PORT}"

    async def fetch_mcp_data(self):
        """Fetch data from MCP servers"""
        async with httpx.AsyncClient() as client:
            # Fetch GitHub MCP data
            github_response = await client.get(f"{self.github_mcp_url}/metrics")
            github_data = github_response.json()
            
            # Fetch Slack MCP data
            slack_response = await client.get(f"{self.slack_mcp_url}/metrics")
            slack_data = slack_response.json()
            
            # Fetch Jira MCP data
            jira_response = await client.get(f"{self.jira_mcp_url}/metrics")
            jira_data = jira_response.json()
            
            return {
                **github_data,
                **slack_data,
                **jira_data
            }

    async def process_input(self, input_text: str, integration_data: Optional[Dict] = None) -> Dict:
        """Process input through the workflow"""
        self.context = {"text": input_text}
        
        # Fetch MCP data
        mcp_data = await self.fetch_mcp_data()
        self.context.update(mcp_data)
        
        # Add any additional integration data
        if integration_data:
            self.context.update(integration_data)
        
        return self.context

    async def get_status(self) -> Dict:
        """Get current workflow status"""
        return {"status": "running", "context": self.context}

    def stop(self):
        """Stop all services"""
        self.is_running = False

# Create global workflow manager instance
workflow_manager = WorkflowManager() 