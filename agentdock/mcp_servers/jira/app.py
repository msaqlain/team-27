from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import base64

app = FastAPI(title="Jira MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class JiraConfig(BaseModel):
    token: str
    email: str
    url: str

class JiraTicket(BaseModel):
    summary: str
    description: Optional[str] = None
    issue_type: str = "Task"
    project_key: str
    priority: Optional[str] = "Medium"
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None

class JiraTicketUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None

# State
jira_config: Optional[JiraConfig] = None

@app.post("/configure")
async def configure_jira(config: JiraConfig):
    """Configure Jira connection with token, email, and URL"""
    global jira_config
    jira_config = config
    return {"status": "success", "message": "Jira configured successfully"}

@app.get("/config")
async def get_config():
    """Get current Jira configuration"""
    if not jira_config:
        raise HTTPException(status_code=404, detail="Jira not configured")
    return {
        "email": jira_config.email,
        "url": jira_config.url,
        "configured": True
    }

@app.post("/deregister")
async def deregister():
    """Deregister the Jira agent"""
    global jira_config
    jira_config = None
    return {"status": "success", "message": "Jira agent deregistered"}

async def jira_request(method: str, endpoint: str, json_data: Optional[Dict] = None):
    """Make an authenticated request to the Jira API"""
    if not jira_config:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    # Create basic auth header with email and token
    auth_str = f"{jira_config.email}:{jira_config.token}"
    auth_bytes = auth_str.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_auth = base64_bytes.decode('ascii')
    
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json"
    }
    
    url = f"{jira_config.url.rstrip('/')}/rest/api/3{endpoint}"
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=json_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code >= 400:
            error_msg = f"Jira API error: {response.status_code}"
            try:
                error_data = response.json()
                if "errorMessages" in error_data and error_data["errorMessages"]:
                    error_msg += f" - {', '.join(error_data['errorMessages'])}"
                elif "errors" in error_data and error_data["errors"]:
                    error_msg += f" - {', '.join(f'{k}: {v}' for k, v in error_data['errors'].items())}"
            except:
                error_msg += f" - {response.text}"
            
            raise HTTPException(status_code=response.status_code, detail=error_msg)
        
        return response.json() if response.content else {"status": "success"}

@app.get("/projects")
async def list_projects():
    """List all Jira projects"""
    result = await jira_request("GET", "/project")
    return {"projects": result, "status": "success"}

@app.get("/tickets")
async def list_tickets(
    project_key: Optional[str] = Query(None, description="Project key to filter tickets"),
    status: Optional[str] = Query(None, description="Status to filter tickets"),
    assignee: Optional[str] = Query(None, description="Assignee to filter tickets"),
    limit: int = Query(50, description="Maximum number of tickets to return")
):
    """List Jira tickets (issues) with optional filters"""
    # Build JQL query
    jql_parts = []
    if project_key:
        jql_parts.append(f"project = {project_key}")
    if status:
        jql_parts.append(f"status = \"{status}\"")
    if assignee:
        if assignee.lower() == "me":
            jql_parts.append("assignee = currentUser()")
        else:
            jql_parts.append(f"assignee = \"{assignee}\"")
    
    jql = " AND ".join(jql_parts) if jql_parts else ""
    
    # Make the API request
    params = {"jql": jql} if jql else {}
    params["maxResults"] = limit
    
    result = await jira_request("GET", f"/search?jql={jql}&maxResults={limit}")
    
    # Extract and format issues
    issues = []
    for issue in result.get("issues", []):
        formatted_issue = {
            "key": issue.get("key"),
            "summary": issue.get("fields", {}).get("summary"),
            "status": issue.get("fields", {}).get("status", {}).get("name"),
            "priority": issue.get("fields", {}).get("priority", {}).get("name"),
            "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName") if issue.get("fields", {}).get("assignee") else None,
            "created": issue.get("fields", {}).get("created"),
            "updated": issue.get("fields", {}).get("updated"),
            "issue_type": issue.get("fields", {}).get("issuetype", {}).get("name")
        }
        issues.append(formatted_issue)
    
    return {"tickets": issues, "total": result.get("total", 0), "status": "success"}

@app.get("/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get details for a specific Jira ticket"""
    result = await jira_request("GET", f"/issue/{ticket_id}")
    
    # Extract and format issue details
    fields = result.get("fields", {})
    issue = {
        "key": result.get("key"),
        "summary": fields.get("summary"),
        "description": fields.get("description"),
        "status": fields.get("status", {}).get("name"),
        "priority": fields.get("priority", {}).get("name"),
        "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
        "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "issue_type": fields.get("issuetype", {}).get("name"),
        "project": fields.get("project", {}).get("key"),
        "labels": fields.get("labels", [])
    }
    
    return {"ticket": issue, "status": "success"}

@app.post("/ticket/create")
async def create_ticket(ticket: JiraTicket):
    """Create a new Jira ticket"""
    # Prepare the request payload
    payload = {
        "fields": {
            "summary": ticket.summary,
            "project": {
                "key": ticket.project_key
            },
            "issuetype": {
                "name": ticket.issue_type
            }
        }
    }
    
    # Add optional fields if they're provided
    if ticket.description:
        payload["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": ticket.description
                        }
                    ]
                }
            ]
        }
    
    if ticket.priority:
        payload["fields"]["priority"] = {
            "name": ticket.priority
        }
    
    if ticket.assignee:
        payload["fields"]["assignee"] = {
            "name": ticket.assignee
        }
    
    if ticket.labels:
        payload["fields"]["labels"] = ticket.labels
    
    # Create the ticket
    result = await jira_request("POST", "/issue", payload)
    
    # Return the created ticket info
    if "key" in result:
        # Fetch the created ticket details
        ticket_details = await get_ticket(result["key"])
        return {
            "key": result["key"],
            "ticket": ticket_details["ticket"],
            "status": "success",
            "message": f"Ticket {result['key']} created successfully"
        }
    
    return {
        "status": "success", 
        "message": "Ticket created successfully",
        "result": result
    }

@app.put("/ticket/{ticket_id}")
async def update_ticket(ticket_id: str, update: JiraTicketUpdate):
    """Update an existing Jira ticket"""
    # Prepare the request payload
    payload = {"fields": {}}
    
    # Add fields that need to be updated
    if update.summary:
        payload["fields"]["summary"] = update.summary
    
    if update.description:
        payload["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": update.description
                        }
                    ]
                }
            ]
        }
    
    if update.priority:
        payload["fields"]["priority"] = {
            "name": update.priority
        }
    
    if update.assignee:
        payload["fields"]["assignee"] = {
            "name": update.assignee
        }
    
    if update.labels:
        payload["fields"]["labels"] = update.labels
    
    # For status changes, we need a separate transition request
    # Which we'll handle below if status is specified
    
    # Only make the update request if there are fields to update
    if payload["fields"]:
        await jira_request("PUT", f"/issue/{ticket_id}", payload)
    
    # Handle status change (transition) if requested
    if update.status:
        # First get available transitions
        transitions = await jira_request("GET", f"/issue/{ticket_id}/transitions")
        transition_id = None
        
        for transition in transitions.get("transitions", []):
            if transition["name"].lower() == update.status.lower():
                transition_id = transition["id"]
                break
        
        if transition_id:
            transition_payload = {
                "transition": {
                    "id": transition_id
                }
            }
            await jira_request("POST", f"/issue/{ticket_id}/transitions", transition_payload)
        else:
            return {
                "status": "partial_success",
                "message": f"Ticket updated but status '{update.status}' is not a valid transition"
            }
    
    # Get the updated ticket details
    ticket_details = await get_ticket(ticket_id)
    
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} updated successfully",
        "ticket": ticket_details["ticket"]
    }

@app.get("/ticket_types")
async def get_ticket_types(project_key: str):
    """Get available issue types for a project"""
    # Get project metadata including issue types
    result = await jira_request("GET", f"/project/{project_key}")
    
    # Extract issue types
    issue_types = []
    if "issueTypes" in result:
        issue_types = [
            {"id": it.get("id"), "name": it.get("name"), "description": it.get("description")}
            for it in result.get("issueTypes", [])
        ]
    
    return {"issue_types": issue_types, "status": "success"}

@app.get("/statuses")
async def get_statuses(project_key: str):
    """Get available statuses for a project"""
    # Get project statuses
    result = await jira_request("GET", f"/project/{project_key}/statuses")
    
    # Format the response
    statuses = []
    for item in result:
        for status in item.get("statuses", []):
            statuses.append({
                "id": status.get("id"),
                "name": status.get("name"),
                "category": status.get("statusCategory", {}).get("name")
            })
    
    return {"statuses": statuses, "status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
