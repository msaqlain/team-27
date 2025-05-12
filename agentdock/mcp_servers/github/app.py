from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import os
from datetime import datetime

app = FastAPI(title="GitHub MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class GitHubConfig(BaseModel):
    token: str

class RepositoryInfo(BaseModel):
    owner: str
    repo: str

class PRSummary(BaseModel):
    pr_number: int
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

class RepoSync(BaseModel):
    branch: str
    status: str
    last_sync: datetime

class CreatePRRequest(BaseModel):
    title: str
    body: str
    head: str
    base: str = "main"

class RepoStats(BaseModel):
    stars: int
    forks: int
    open_issues: int
    watchers: int
    language: str
    description: str
    last_updated: datetime

# State
github_token: Optional[str] = None

@app.post("/configure")
async def configure_github(config: GitHubConfig):
    """Configure GitHub connection with token"""
    global github_token
    github_token = config.token
    return {"status": "success", "message": "GitHub configuration updated"}

@app.get("/config")
async def get_config():
    """Get current GitHub configuration"""
    global github_token
    if not github_token:
        raise HTTPException(status_code=404, detail="GitHub not configured")
    return {"token": github_token}

@app.get("/repos")
async def list_repositories():
    """List all repositories the user has access to"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch repositories")
        
        return response.json()

@app.get("/{owner}/{repo}/prs")
async def list_prs(owner: str, repo: str):
    """List all PRs in the specified repository"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch PRs")
        
        return response.json()

@app.get("/{owner}/{repo}/pr/{pr_number}/summary")
async def get_pr_summary(owner: str, repo: str, pr_number: int):
    """Get summary of a specific PR"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch PR")
        
        pr_data = response.json()
        return PRSummary(
            pr_number=pr_data["number"],
            title=pr_data["title"],
            description=pr_data["body"],
            status=pr_data["state"],
            created_at=datetime.strptime(pr_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            updated_at=datetime.strptime(pr_data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
        )

@app.post("/{owner}/{repo}/sync")
async def sync_repo(owner: str, repo: str, branch: str = "main"):
    """Sync repository with remote"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    # In a real implementation, this would use git commands to sync the repo
    return RepoSync(
        branch=branch,
        status="synced",
        last_sync=datetime.now()
    )

@app.post("/{owner}/{repo}/workflow/{workflow_id}/trigger")
async def trigger_workflow(owner: str, repo: str, workflow_id: str):
    """Trigger a GitHub Actions workflow"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            headers=headers,
            json={"ref": "main"}
        )
        
        if response.status_code != 204:
            raise HTTPException(status_code=response.status_code, detail="Failed to trigger workflow")
        
        return {"status": "success", "message": f"Workflow {workflow_id} triggered"}

@app.post("/{owner}/{repo}/pr/create")
async def create_pr(owner: str, repo: str, pr_request: CreatePRRequest):
    """Create a new pull request"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers,
            json={
                "title": pr_request.title,
                "body": pr_request.body,
                "head": pr_request.head,
                "base": pr_request.base
            }
        )
        
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail="Failed to create PR")
        
        return response.json()

@app.get("/{owner}/{repo}/stats")
async def get_repo_stats(owner: str, repo: str):
    """Get repository statistics"""
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch repository stats")
        
        repo_data = response.json()
        return RepoStats(
            stars=repo_data["stargazers_count"],
            forks=repo_data["forks_count"],
            open_issues=repo_data["open_issues_count"],
            watchers=repo_data["watchers_count"],
            language=repo_data["language"],
            description=repo_data["description"],
            last_updated=datetime.strptime(repo_data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
