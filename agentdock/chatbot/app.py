from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import os
from datetime import datetime
import json
import logging
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentDock Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client with environment variable
groq_api_key = "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"
if not groq_api_key:
    logger.error("GROQ_API_KEY environment variable is not set")
    raise ValueError("GROQ_API_KEY environment variable is not set")

logger.info("Initializing Groq client...")
client = Groq(api_key=groq_api_key)

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[Dict] = None

# GitHub MCP Server endpoints - will be configured by Dapr
GITHUB_MCP_BASE_URL = os.getenv("GITHUB_MCP_URL", "http://localhost:8001")
logger.info(f"GitHub MCP URL: {GITHUB_MCP_BASE_URL}")

async def check_repo_visibility(owner: str, repo: str) -> bool:
    """Check if a repository is public"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if response.status_code == 200:
                return not response.json().get("private", True)
            return False
    except Exception as e:
        logger.error(f"Error checking repo visibility: {str(e)}")
        return False

async def get_github_token() -> Optional[str]:
    """Get GitHub token from MCP server configuration"""
    try:
        logger.info(f"Attempting to fetch GitHub token from MCP server at {GITHUB_MCP_BASE_URL}/config")
        async with httpx.AsyncClient() as client:
            # First try to get the configuration
            response = await client.get(f"{GITHUB_MCP_BASE_URL}/config")
            logger.info(f"MCP server response status: {response.status_code}")
            logger.info(f"MCP server response body: {response.text}")
            
            if response.status_code == 200:
                try:
                    config = response.json()
                    token = config.get("token")
                    if token:
                        logger.info("Successfully retrieved GitHub token from MCP server")
                        return token
                    else:
                        logger.error("No token found in MCP server configuration")
                        return None
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse MCP server response as JSON: {e}")
                    return None
            elif response.status_code == 404:
                logger.error("GitHub not configured. Please configure first using POST /configure")
                return None
            else:
                logger.error(f"Failed to get configuration from MCP server: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error getting GitHub token from MCP server: {str(e)}")
        return None

async def call_github_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, use_token: bool = True) -> Dict:
    """Call GitHub API endpoint"""
    try:
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Add token if using authenticated requests
        if use_token:
            token = await get_github_token()
            if not token:
                logger.error("No GitHub token available")
                raise HTTPException(
                    status_code=400, 
                    detail="GitHub token not configured. Please configure using the MCP server first. Make sure to call POST http://localhost:8001/configure with your token."
                )
            headers["Authorization"] = f"token {token}"
            logger.info("Added GitHub token to request headers")
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/{endpoint}"
            logger.info(f"Calling GitHub API endpoint: {url}")
            
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"GitHub API error: {response.text}")
            
            return response.json()
    except Exception as e:
        logger.error(f"Error calling GitHub API: {str(e)}")
        raise

def extract_github_params(message: str) -> Dict:
    """Extract repository and PR information from natural language"""
    try:
        prompt = f"""
        You are a GitHub information extractor. Extract information from this message: "{message}"
        
        If the message is a general conversation or greeting, return:
        {{"action": "conversation"}}
        
        For GitHub-related queries, return a JSON object with these fields if present:
        - owner: repository owner (username or organization)
        - repo: repository name
        - pr_number: pull request number (if mentioned)
        - action: one of [list_prs, get_pr_summary, get_stats, get_repo_info, list_my_repos]
        
        Examples:
        1. Input: "Hello, how are you?"
           Output: {{"action": "conversation"}}
        
        2. Input: "Show me all pull requests in microsoft/vscode repository"
           Output: {{"owner": "microsoft", "repo": "vscode", "action": "list_prs"}}
        
        3. Input: "What is the summary of PR #123 in microsoft/vscode?"
           Output: {{"owner": "microsoft", "repo": "vscode", "pr_number": 123, "action": "get_pr_summary"}}
        
        4. Input: "Show me the statistics for the microsoft/vscode repository"
           Output: {{"owner": "microsoft", "repo": "vscode", "action": "get_stats"}}
        
        5. Input: "Tell me about the vscode repository"
           Output: {{"owner": "microsoft", "repo": "vscode", "action": "get_repo_info"}}
        
        6. Input: "list all my repositories"
           Output: {{"action": "list_my_repos"}}
        
        Only include fields that are present in the message. Always include the action field.
        Return ONLY the JSON object, no other text.
        """
        
        logger.info("Calling Groq API to extract parameters...")
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a GitHub information extractor. Always return valid JSON objects only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content.strip()
        logger.info(f"Raw Groq response: {response_content}")
        
        try:
            # Try to parse the response as JSON
            result = json.loads(response_content)
            
            # Validate required fields
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            if "action" not in result:
                raise ValueError("Missing 'action' field in response")
            
            # Only require owner and repo for non-conversation and non-list_my_repos actions
            if result["action"] not in ["conversation", "list_my_repos"] and ("owner" not in result or "repo" not in result):
                raise ValueError("Missing 'owner' or 'repo' field in response")
            
            logger.info(f"Successfully extracted parameters: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            logger.error(f"Raw response content: {response_content}")
            return {"action": "conversation"}
        except ValueError as e:
            logger.error(f"Invalid response format: {e}")
            return {"action": "conversation"}
            
    except Exception as e:
        logger.error(f"Error in extract_github_params: {str(e)}")
        return {"action": "conversation"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process natural language message and interact with GitHub"""
    try:
        logger.info(f"Received chat message: {message.message}")
        
        # Extract GitHub parameters
        params = extract_github_params(message.message)
        
        if not params:
            logger.warning("Could not extract parameters from message")
            return ChatResponse(
                response="I couldn't understand what GitHub information you want. Please try rephrasing your request.",
                action_taken=None
            )
        
        action = params.get("action")
        
        # Handle general conversation
        if action == "conversation":
            return ChatResponse(
                response="Hello! I'm your GitHub assistant. I can help you with:\n"
                        "• Viewing repository information\n"
                        "• Checking pull requests\n"
                        "• Getting repository statistics\n"
                        "• Listing your repositories\n\n"
                        "Just ask me about any GitHub repository or say 'list all my repositories' to see your own repositories.",
                action_taken={"action": "conversation"}
            )
        
        owner = params.get("owner")
        repo = params.get("repo")
        pr_number = params.get("pr_number")
        
        logger.info(f"Extracted parameters - action: {action}, owner: {owner}, repo: {repo}, pr_number: {pr_number}")
        
        # Handle list_my_repos action
        if action == "list_my_repos":
            try:
                # Get user's repositories
                result = await call_github_api("user/repos", use_token=True)
                
                # Format the response
                repos = []
                for repo in result:
                    repos.append({
                        "name": repo["name"],
                        "description": repo["description"],
                        "url": repo["html_url"],
                        "private": repo["private"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"]
                    })
                
                if not repos:
                    return ChatResponse(
                        response="You don't have any repositories yet.",
                        action_taken={"action": "list_my_repos", "result": []}
                    )
                
                return ChatResponse(
                    response=f"Here are your repositories:\n" + "\n".join([
                        f"• {r['name']} ({'Private' if r['private'] else 'Public'}) - {r['description'] or 'No description'}\n"
                        f"  Stars: {r['stars']}, Forks: {r['forks']}\n"
                        f"  URL: {r['url']}"
                        for r in repos
                    ]),
                    action_taken={"action": "list_my_repos", "result": repos}
                )
            except Exception as e:
                logger.error(f"Error listing repositories: {str(e)}")
                return ChatResponse(
                    response="To access your repositories, you need to configure GitHub first. Please use:\n\n"
                            "POST http://localhost:8001/configure\n"
                            "Content-Type: application/json\n"
                            '{"token": "your_github_token"}',
                    action_taken=None
                )
        
        # Handle other actions
        if not owner or not repo:
            return ChatResponse(
                response="I need more information about which repository and action you want to perform.",
                action_taken=None
            )
        
        # Check if repository is public
        is_public = await check_repo_visibility(owner, repo)
        
        if not is_public:
            # For private repositories, check if GitHub is configured
            token = await get_github_token()
            if not token:
                return ChatResponse(
                    response=f"To access private repository {owner}/{repo}, you need to configure GitHub first. Please use:\n\n"
                            "POST http://localhost:8001/configure\n"
                            "Content-Type: application/json\n"
                            '{"token": "your_github_token"}',
                    action_taken=None
                )
        
        # Map actions to GitHub API endpoints
        if action == "list_prs":
            result = await call_github_api(f"repos/{owner}/{repo}/pulls", use_token=not is_public)
            return ChatResponse(
                response=f"Here are the pull requests for {owner}/{repo}:",
                action_taken={"action": "list_prs", "result": result}
            )
            
        elif action == "get_pr_summary" and pr_number:
            result = await call_github_api(f"repos/{owner}/{repo}/pulls/{pr_number}", use_token=not is_public)
            return ChatResponse(
                response=f"Here's the summary of PR #{pr_number} in {owner}/{repo}:",
                action_taken={"action": "get_pr_summary", "result": result}
            )
            
        elif action == "get_stats":
            result = await call_github_api(f"repos/{owner}/{repo}", use_token=not is_public)
            return ChatResponse(
                response=f"Here are the statistics for {owner}/{repo}:",
                action_taken={"action": "get_stats", "result": result}
            )
            
        elif action == "get_repo_info":
            result = await call_github_api(f"repos/{owner}/{repo}", use_token=not is_public)
            return ChatResponse(
                response=f"Here's information about {owner}/{repo}:",
                action_taken={"action": "get_repo_info", "result": result}
            )
            
        else:
            return ChatResponse(
                response=f"I understand you want to {action} for {owner}/{repo}, but I need more information to proceed.",
                action_taken=None
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            action_taken=None
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 