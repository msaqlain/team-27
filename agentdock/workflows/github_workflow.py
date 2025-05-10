from dapr.workflow import WorkflowContext, WorkflowActivity, Workflow
from dapr.workflow.runtime import WorkflowRuntime
from dapr.clients import DaprClient
import asyncio
from typing import List, Dict
import json

class GitHubWorkflow(Workflow):
    def __init__(self):
        self.github_app_id = "GithubApp"

    async def run(self, context: WorkflowContext, action: str, params: Dict = None) -> Dict:
        """Main workflow entry point"""
        if params is None:
            params = {}

        if action == "list_prs":
            return await self.list_prs(context)
        elif action == "get_pr_summary":
            return await self.get_pr_summary(context, params.get("pr_number"))
        elif action == "sync_repo":
            return await self.sync_repo(context, params.get("branch", "main"))
        elif action == "trigger_workflow":
            return await self.trigger_workflow(context, params.get("workflow_id"))
        else:
            raise ValueError(f"Unknown action: {action}")

    async def list_prs(self, context: WorkflowContext) -> Dict:
        """List all PRs in the repository"""
        async with DaprClient() as d:
            response = await d.invoke_method(
                self.github_app_id,
                "prs",
                data=b"",
                http_verb="GET"
            )
            return json.loads(response.data)

    async def get_pr_summary(self, context: WorkflowContext, pr_number: int) -> Dict:
        """Get summary of a specific PR"""
        async with DaprClient() as d:
            response = await d.invoke_method(
                self.github_app_id,
                f"pr/{pr_number}/summary",
                data=b"",
                http_verb="GET"
            )
            return json.loads(response.data)

    async def sync_repo(self, context: WorkflowContext, branch: str) -> Dict:
        """Sync repository with remote"""
        async with DaprClient() as d:
            response = await d.invoke_method(
                self.github_app_id,
                "sync",
                data=json.dumps({"branch": branch}).encode(),
                http_verb="POST"
            )
            return json.loads(response.data)

    async def trigger_workflow(self, context: WorkflowContext, workflow_id: str) -> Dict:
        """Trigger a GitHub Actions workflow"""
        async with DaprClient() as d:
            response = await d.invoke_method(
                self.github_app_id,
                f"workflow/{workflow_id}/trigger",
                data=b"",
                http_verb="POST"
            )
            return json.loads(response.data)

def register_workflows(runtime: WorkflowRuntime):
    """Register all workflows"""
    runtime.register_workflow(GitHubWorkflow)

if __name__ == "__main__":
    # Create and start the workflow runtime
    runtime = WorkflowRuntime()
    register_workflows(runtime)
    runtime.start() 