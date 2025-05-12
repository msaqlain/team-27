from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Union
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

# MCP Server endpoints - will be configured by Dapr
GITHUB_MCP_BASE_URL = os.getenv("GITHUB_MCP_URL", "http://localhost:8001")
SLACK_MCP_BASE_URL = os.getenv("SLACK_MCP_URL", "http://localhost:8003")
JIRA_MCP_BASE_URL = os.getenv("JIRA_MCP_URL", "http://localhost:8004")
logger.info(f"GitHub MCP URL: {GITHUB_MCP_BASE_URL}")
logger.info(f"Slack MCP URL: {SLACK_MCP_BASE_URL}")

# GitHub configuration
GITHUB_API_BASE_URL = "https://api.github.com"
# Read GitHub token from environment variable for security
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# If not set, you'll need to provide it through the settings UI

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
    """Get GitHub token from environment or a secure place"""
    if GITHUB_TOKEN:
        logger.info("Using GitHub token from environment variables")
        return GITHUB_TOKEN
    
    # Fallback to MCP server for backward compatibility
    try:
        logger.info(f"Attempting to fetch GitHub token from MCP server at {GITHUB_MCP_BASE_URL}/config")
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{GITHUB_MCP_BASE_URL}/config")
                if response.status_code == 200:
                    config = response.json()
                    token = config.get("token")
                    if token:
                        logger.info("Successfully retrieved GitHub token from MCP server")
                        return token
            except Exception as e:
                logger.error(f"Error connecting to MCP server: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting GitHub token: {str(e)}")
    
    logger.warning("No GitHub token available. Some GitHub operations will be limited to public resources.")
    return None

async def get_slack_token(slack_mcp_url: str) -> Optional[str]:
    """Get Slack token from Slack MCP server configuration"""
    try:
        logger.info(f"Attempting to fetch Slack token from MCP server at {slack_mcp_url}/config")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{slack_mcp_url}/config")
            logger.info(f"Slack MCP server response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    config = response.json()
                    token = config.get("token")
                    if token:
                        logger.info("Successfully retrieved Slack token from MCP server")
                        return token
                    else:
                        logger.error("No token found in Slack MCP server configuration")
                        return None
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Slack MCP server response as JSON: {e}")
                    return None
            elif response.status_code == 404:
                logger.error("Slack not configured. Please configure first using POST /configure")
                return None
            else:
                logger.error(f"Failed to get configuration from Slack MCP server: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error getting Slack token from MCP server: {str(e)}")
        return None

async def call_github_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, use_token: bool = True) -> Dict:
    """Call GitHub API endpoint directly"""
    try:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"  # Use a stable API version
        }
        
        # Add token if using authenticated requests
        if use_token:
            token = await get_github_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.info("Added GitHub token to request headers")
            elif endpoint.startswith("user") or "private" in endpoint:
                # If endpoint requires authentication and no token is available
                logger.error("No GitHub token available for authenticated endpoint")
                raise HTTPException(
                    status_code=401, 
                    detail="GitHub token not configured. Authentication required for this operation."
                )
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{GITHUB_API_BASE_URL}/{endpoint}"
            logger.info(f"Calling GitHub API endpoint: {url}")
            
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # GitHub API returns 200-204 for success depending on the endpoint
                if response.status_code >= 200 and response.status_code < 300:
                    if response.status_code == 204:  # No content
                        return {"status": "success", "message": "Operation completed successfully"}
                    
                    # Some endpoints may return empty response
                    if not response.text:
                        return {"status": "success", "message": "Operation completed successfully"}
                    
                    return response.json()
                else:
                    error_message = f"GitHub API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_message += f" - {error_data['message']}"
                    except Exception:
                        error_message += f" - {response.text}"
                    
                    logger.error(error_message)
                    raise HTTPException(status_code=response.status_code, detail=error_message)
            
            except httpx.ReadTimeout:
                logger.error("GitHub API request timed out")
                raise HTTPException(status_code=504, detail="GitHub API request timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling GitHub API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling GitHub API: {str(e)}")

async def call_slack_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, slack_mcp_url: str = SLACK_MCP_BASE_URL) -> Dict:
    """Call Slack API endpoint through the MCP server"""
    try:
        logger.info(f"Calling Slack MCP server: {slack_mcp_url}")
        
        # Map Slack API endpoints to MCP server endpoints
        mcp_endpoint = ""
        if endpoint == "conversations.list":
            mcp_endpoint = "/channels"
        elif endpoint == "chat.postMessage":
            mcp_endpoint = "/message"
            # Check if we have the required data
            if not data.get("channel") or not data.get("text"):
                raise ValueError("Missing channel or text for Slack message")
        else:
            logger.error(f"Unsupported Slack endpoint: {endpoint}")
            raise ValueError(f"Unsupported Slack endpoint: {endpoint}")
        
        async with httpx.AsyncClient() as client:
            url = f"{slack_mcp_url}{mcp_endpoint}"
            logger.info(f"Calling Slack MCP endpoint: {url}")
            
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                # Transform the data format if needed
                if mcp_endpoint == "/message":
                    mcp_data = {
                        "channel": data.get("channel"),
                        "text": data.get("text")
                    }
                else:
                    mcp_data = data
                
                response = await client.post(url, json=mcp_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                logger.error(f"Slack MCP error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Slack MCP error: {response.text}")
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Error calling Slack MCP API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling Slack MCP: {str(e)}")

def determine_intent(message: str) -> Dict:
    """Determine if the message is related to GitHub, Slack, Jira, or a combination"""
    try:
        prompt = f"""
        You are an intent classifier for a chatbot that handles GitHub, Slack, and Jira operations. 
        Analyze this message: "{message}"
        
        Return a JSON object with:
        1. "platform": One of "github", "slack", "jira", "github_slack", "conversation" (for general chat)
        2. "confidence": A number between 0 and 1 indicating your confidence
        
        If platform is "github" or involves GitHub, include these fields:
        - github_action: one of [list_prs, get_pr_summary, get_stats, create_pr, list_my_repos]
        - owner: repository owner (if mentioned)
        - repo: repository name (if mentioned)
        - pr_number: pull request number (if mentioned)
        - pr_title: pull request title (if mentioned)
        - pr_body: pull request body (if mentioned)
        - pr_head: pull request head (if mentioned)
        - pr_base: pull request base branch (if mentioned)
        
        If platform is "slack" or involves Slack, include these fields:
        - slack_action: one of [list_channels, send_message, get_conversation_history]
        - channel: channel name or ID (if mentioned)
        - message_content: content of message to send (if applicable)
        - time_range: time range for history (if applicable)
        
        If platform is "jira" or involves Jira, include these fields:
        - jira_action: one of [list_projects, list_tickets, get_ticket, create_ticket, update_ticket]
        - project_key: project key (if mentioned)
        - ticket_id: ticket ID or key (if mentioned)
        - summary: ticket summary (if mentioned)
        - description: ticket description (if mentioned)
        - status: ticket status (if mentioned)
        - priority: ticket priority (if mentioned)
        - assignee: ticket assignee (if mentioned)
        - issue_type: issue type (if mentioned)
        - labels: ticket labels (if mentioned)
        
        Return ONLY the JSON object, no other text.
        """
        
        logger.info("Calling Groq API to determine intent...")
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an intent classifier for GitHub, Slack, and Jira operations. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content.strip()
        logger.info(f"Raw Groq response: {response_content}")
        
        try:
            # Parse the response as JSON
            result = json.loads(response_content)
            
            # Validate required fields
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            if "platform" not in result:
                raise ValueError("Missing 'platform' field in response")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            logger.error(f"Raw response content: {response_content}")
            return {"platform": "conversation"}
        except ValueError as e:
            logger.error(f"Invalid response format: {e}")
            return {"platform": "conversation"}
            
    except Exception as e:
        logger.error(f"Error in determine_intent: {str(e)}")
        return {"platform": "conversation"}
    
class CreatePRRequest(BaseModel):
    title: str
    body: str
    head: str
    base: str = "main"

async def handle_github_request(params: Dict, github_mcp_url: str) -> Dict:
    """Handle GitHub-related requests"""
    action = params.get("github_action")
    owner = params.get("owner")
    repo = params.get("repo")
    pr_number = params.get("pr_number")
    pr_title = params.get("pr_title")
    pr_body = params.get("pr_body")
    pr_head = params.get("pr_head")
    pr_base = params.get("pr_base")
    
    # Handle list_my_repos action
    if action == "list_my_repos":
        try:
        # Use async context manager for the HTTP client
            async with httpx.AsyncClient() as client:
                # Print for debugging
                print("Attempting to fetch repositories...")
                
                # Make the GET request
                response = await client.get(f"{github_mcp_url}/repos")
                
                # Check if the response was successful
                response.raise_for_status()
                
                # Parse JSON response
                result = response.json()
                
                # Print raw result for debugging
                print(f"Received {len(result)} repositories")
                
                # Format the repositories
                repos = []
                for repo_data in result:
                    # Safely extract repository information with default values
                    repos.append({
                        "name": repo_data.get("name", "Unknown Repository"),
                        "description": repo_data.get("description", "No description"),
                        "url": repo_data.get("html_url", ""),
                        "private": repo_data.get("private", False),
                        "stars": repo_data.get("stargazers_count", 0),
                        "forks": repo_data.get("forks_count", 0)
                    })
            
            # Handle empty repository list
                if not repos:
                    return {
                        "response": "You don't have any repositories yet.",
                        "action_taken": {"action": "list_my_repos", "result": []}
                    }
            
            # Format response with repository details
                return {
                    "response": "Here are your repositories:\n" + "\n".join([
                        f"• {r['name']} ({'Private' if r['private'] else 'Public'}) - {r['description']}\n"
                        f"  Stars: {r['stars']}, Forks: {r['forks']}\n"
                        f"  URL: {r['url']}"
                        for r in repos
                    ]),
                    "action_taken": {"action": "list_my_repos", "result": repos}
                }
        except Exception as e:
            # Catch-all for any other unexpected errors
            logging.error(f"Unexpected error listing repositories: {str(e)}")
            return {
                "response": "To access your repositories, you need to configure GitHub first. Please use:\n\n"
                        "POST http://localhost:8001/configure\n"
                        "Content-Type: application/json\n"
                        '{"token": "your_github_token"}',
                "action_taken": None
            }
    
    # Handle other actions that require owner and repo
    if not owner or not repo:
        return {
            "response": "I need more information about which repository and action you want to perform.",
            "action_taken": None
        }
    
    # Check if repository is public
    is_public = await check_repo_visibility(owner, repo)
    
    if not is_public:
        # For private repositories, check if GitHub is configured
        token = await get_github_token()
        if not token:
            return {
                "response": f"To access private repository {owner}/{repo}, you need to configure GitHub first. Please use:\n\n"
                        "POST http://localhost:8001/configure\n"
                        "Content-Type: application/json\n"
                        '{"token": "your_github_token"}',
                "action_taken": None
            }
    
    # Map actions to GitHub API endpoints
    if action == "list_prs":
        # result = await call_github_api(f"repos/{owner}/{repo}/pulls", use_token=not is_public)
        async with httpx.AsyncClient() as client:
            # First try to get the configuration
            response = await client.get(f"{github_mcp_url}/{owner}/{repo}/prs")
            response.raise_for_status()
            result = response.json()
            if not result:
                return {
                    "response": f"No open pull requests found for {owner}/{repo}.",
                    "action_taken": {"action": "list_prs", "result": []}
                }
        
            pr_list = "\n".join([
                f"• #{pr['number']} - {pr['title']} by {pr['user']['login']}\n"
                f"  Status: {pr['state']}, Created: {pr['created_at']}\n"
                f"  URL: {pr['html_url']}"
                for pr in result
            ])
        
            return {
                "response": f"Here are the pull requests for {owner}/{repo}:\n\n{pr_list}",
                "action_taken": {"action": "list_prs", "result": result},
                "raw_data": result  # Store the raw data for potential cross-platform actions
            }
        
    elif action == "get_pr_summary" and pr_number:
        # result = await call_github_api(f"repos/{owner}/{repo}/pulls/{pr_number}", use_token=not is_public)
        async with httpx.AsyncClient() as client:
            # First try to get the configuration
            response = await client.get(f"{github_mcp_url}/{owner}{repo}/prs/{pr_number}/summary")
            response.raise_for_status()
            result = response.json()
        
        # Format PR summary
            pr_summary = (
                f"PR #{pr_number}: {result['title']}\n"
                f"Author: {result['user']['login']}\n"
                f"Status: {result['state'].upper()}\n"
                f"Created: {result['created_at']}\n"
                f"Description: {result['body'] or 'No description provided'}\n"
                f"URL: {result['html_url']}"
            )
        
            return {
                "response": f"Here's the summary of PR #{pr_number} in {owner}/{repo}:\n\n{pr_summary}",
                "action_taken": {"action": "get_pr_summary", "result": result},
                "raw_data": result  # Store the raw data for potential cross-platform actions
            }
            
    elif action == "get_stats":
        async with httpx.AsyncClient() as client:
            # First try to get the configuration
            response = await client.get(f"{github_mcp_url}/{owner}/{repo}/stats")
            response.raise_for_status()
            result = response.json()
        
        # Format repo stats
            repo_stats = (
                f"Repository: {result['full_name']}\n"
                f"Description: {result['description'] or 'No description'}\n"
                f"Stars: {result['stargazers_count']}\n"
                f"Forks: {result['forks_count']}\n"
                f"Open Issues: {result['open_issues_count']}\n"
                f"Default Branch: {result['default_branch']}\n"
                f"License: {result.get('license', {}).get('name', 'None')}\n"
                f"Created: {result['created_at']}\n"
                f"Last Updated: {result['updated_at']}\n"
                f"URL: {result['html_url']}"
            )
        
            return {
                "response": f"Here are the statistics for {owner}/{repo}:\n\n{repo_stats}",
                "action_taken": {"action": "get_stats", "result": result}
            }
        
    elif action == "create_pr":
        async with httpx.AsyncClient() as client:
            # First try to get the configuration
            body = CreatePRRequest(
                title=pr_title,
                body=pr_body,
                head=pr_head,
                base=pr_base
            )
            result = await client.post(f"{github_mcp_url}/{owner}/{repo}/pr/create",
                json=body.dict())
        
        return {
            "response": f"PR created",
            "action_taken": {"action": "get_repo_info", "result": result}
        }
        
    else:
        return {
            "response": f"I understand you want to {action} for {owner}/{repo}, but I need more information to proceed.",
            "action_taken": None
        }

async def handle_slack_request(params: Dict, slack_mcp_url: str) -> Dict:
    """Handle Slack-related requests"""
    action = params.get("slack_action")
    channel = params.get("channel")
    message_content = params.get("message_content")
    time_range = params.get("time_range")
    
    # Check if Slack is configured
    token = await get_slack_token(slack_mcp_url)
    if not token:
        return {
            "response": "To use Slack functionality, you need to configure Slack first. Please use:\n\n"
                     "POST http://localhost:8003/configure\n"
                     "Content-Type: application/json\n"
                     '{"token": "your_slack_token"}',
            "action_taken": None
        }
    
    # Handle list_channels action
    if action == "list_channels":
        try:
            result = await call_slack_api("conversations.list", method="GET", data={"types": "public_channel,private_channel"})
            
            # Extract channels from the result, handling different possible response formats
            channels = []
            if isinstance(result, dict):
                channels = result.get("channels", [])
            elif isinstance(result, list):
                channels = result  # In case the MCP server returns a direct list
            
            if not channels:
                return {
                    "response": "No channels found in your Slack workspace.",
                    "action_taken": {"action": "list_channels", "result": []}
                }
            
            # Format the channel list for display
            channels_list = "\n".join([
                f"• #{channel.get('name', 'unknown')} ({channel.get('id', 'unknown')}) - {'Private' if channel.get('is_private', False) else 'Public'}"
                for channel in channels
            ])
            
            return {
                "response": f"Here are the channels in your Slack workspace:\n\n{channels_list}",
                "action_taken": {"action": "list_channels", "result": channels}
            }
        except Exception as e:
            logger.error(f"Error listing Slack channels: {str(e)}")
            return {
                "response": f"Error listing Slack channels: {str(e)}",
                "action_taken": None
            }
    
    # Handle send_message action
    elif action == "send_message":
        if not channel:
            return {
                "response": "I need a channel name or ID to send a message.",
                "action_taken": None
            }
        
        if not message_content:
            return {
                "response": "I need message content to send to the Slack channel.",
                "action_taken": None
            }
        
        try:
            result = await call_slack_api(
                "chat.postMessage", 
                method="POST", 
                data={
                    "channel": channel,
                    "text": message_content,
                    "unfurl_links": True
                }
            )
            
            return {
                "response": f"Message successfully sent to {channel}!",
                "action_taken": {"action": "send_message", "channel": channel, "result": result}
            }
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return {
                "response": f"Error sending message to Slack: {str(e)}",
                "action_taken": None
            }
    
    # Handle get_conversation_history action
    elif action == "get_conversation_history":
        if not channel:
            return {
                "response": "I need a channel name or ID to get conversation history.",
                "action_taken": None
            }
        
        try:
            params = {"channel": channel, "limit": 10}
            if time_range:
                # Process time_range if provided
                pass
                
            result = await call_slack_api("conversations.history", method="GET", data=params)
            
            messages = result.get("messages", [])
            if not messages:
                return {
                    "response": f"No messages found in {channel}.",
                    "action_taken": {"action": "get_conversation_history", "result": []}
                }
            
            # Format the conversation history
            messages_list = "\n\n".join([
                f"*{msg.get('user', 'Unknown')} at {msg.get('ts', 'Unknown time')}:*\n{msg.get('text', 'No text')}"
                for msg in messages
            ])
            
            return {
                "response": f"Here are the recent messages in {channel}:\n\n{messages_list}",
                "action_taken": {"action": "get_conversation_history", "result": messages}
            }
        except Exception as e:
            logger.error(f"Error getting Slack conversation history: {str(e)}")
            return {
                "response": f"Error getting Slack conversation history: {str(e)}",
                "action_taken": None
            }
    
    else:
        return {
            "response": f"I understand you want to perform a Slack action, but I need more information to proceed.",
            "action_taken": None
        }

async def handle_cross_platform_action(github_result: Dict, slack_params: Dict, slack_mcp_url: str) -> Dict:
    """Handle actions that involve both GitHub and Slack"""
    try:
        # Check if we have raw GitHub data to send to Slack
        if "raw_data" not in github_result:
            return {
                "response": "I couldn't perform the cross-platform action because the GitHub data is missing.",
                "action_taken": None
            }
        
        github_data = github_result.get("raw_data")
        slack_action = slack_params.get("slack_action")
        channel = slack_params.get("channel")
        
        # If no channel specified, request one
        if not channel:
            return {
                "response": "To complete this action, I need a Slack channel to send the information to. Please specify a channel.",
                "action_taken": None
            }
        
        # Format GitHub data for Slack based on what data we have
        if "title" in github_data and "html_url" in github_data:  # It's likely a PR
            # Format PR data for Slack
            message_content = (
                f"*Pull Request Summary: <{github_data['html_url']}|#{github_data['number']}: {github_data['title']}>*\n"
                f"*Repository:* {github_data['base']['repo']['full_name']}\n"
                f"*Author:* {github_data['user']['login']}\n"
                f"*Status:* {github_data['state'].upper()}\n"
                f"*Created:* {github_data['created_at']}\n\n"
                f"*Description:*\n{github_data['body'] or 'No description provided'}"
            )
        elif isinstance(github_data, list) and len(github_data) > 0 and "number" in github_data[0]:  # It's likely a list of PRs
            # Format PR list for Slack
            prs_text = "\n".join([
                f"• <{pr['html_url']}|#{pr['number']}: {pr['title']}> by {pr['user']['login']} ({pr['state']})"
                for pr in github_data[:5]  # Limit to first 5 for readability
            ])
            message_content = f"*Pull Requests in {github_data[0]['base']['repo']['full_name']}*\n\n{prs_text}"
            if len(github_data) > 5:
                message_content += f"\n\n_...and {len(github_data) - 5} more_"
        else:
            # Generic formatting if we're not sure what the data is
            message_content = f"GitHub information: ```{json.dumps(github_result['response'], indent=2)}```"
        
        # Send to Slack
        result = await call_slack_api(
            "chat.postMessage", 
            method="POST", 
            data={
                "channel": channel,
                "text": message_content,
                "parse": "full",
                "unfurl_links": True
            },
            slack_mcp_url=slack_mcp_url
        )
        
        return {
            "response": f"Successfully sent the GitHub information to Slack channel {channel}!",
            "action_taken": {
                "action": "cross_platform",
                "github_action": github_result.get("action_taken", {}).get("action"),
                "slack_action": "send_message",
                "result": result
            }
        }
    except Exception as e:
        logger.error(f"Error in cross-platform action: {str(e)}")
        return {
            "response": f"Error performing cross-platform action: {str(e)}",
            "action_taken": None
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process natural language message and interact with GitHub and/or Slack"""
    try:
        logger.info(f"Received chat message: {message.message}")
        
        # Get MCP URLs from context if provided
        context = message.context or {}
        github_mcp_url = context.get("github_mcp_url", GITHUB_MCP_BASE_URL)
        slack_mcp_url = context.get("slack_mcp_url", SLACK_MCP_BASE_URL)
        jira_mcp_url = context.get("jira_mcp_url", JIRA_MCP_BASE_URL)
        
        logger.info(f"Using GitHub MCP URL: {github_mcp_url}")
        logger.info(f"Using Slack MCP URL: {slack_mcp_url}")
        logger.info(f"Using Jira MCP URL: {jira_mcp_url}")
        
        # Determine intent (GitHub, Slack, Jira, or combination)
        intent = determine_intent(message.message)
        platform = intent.get("platform", "conversation")
        
        logger.info(f"Determined platform: {platform}")
        
        # Handle general conversation
        if platform == "conversation":
            return ChatResponse(
                response="Hello! I'm your assistant. I can help you with:\n"
                        "• GitHub: View repositories, check pull requests, get repository statistics\n"
                        "• Slack: List channels, send messages, get conversation history\n"
                        "• Jira: List projects, view tickets, create and update tickets\n\n"
                        "Just let me know what you'd like to do!",
                action_taken={"action": "conversation"}
            )
        
        # Handle GitHub-only requests
        elif platform == "github":
            result = await handle_github_request(intent, github_mcp_url)
            return ChatResponse(
                response=result["response"],
                action_taken=result["action_taken"]
            )
        
        # Handle Slack-only requests
        elif platform == "slack":
            result = await handle_slack_request(intent, slack_mcp_url)
            return ChatResponse(
                response=result["response"],
                action_taken=result["action_taken"]
            )
        
        # Handle Jira-only requests
        elif platform == "jira":
            result = await handle_jira_request(intent, jira_mcp_url)
            return ChatResponse(
                response=result["response"],
                action_taken=result["action_taken"]
            )
        
        # Handle cross-platform requests (GitHub and Slack)
        elif platform == "github_slack":
            # First handle the GitHub part
            github_result = await handle_github_request(intent, github_mcp_url)
            
            # Then handle the Slack part
            if "slack_action" in intent and intent["slack_action"] == "send_message":
                # If the intent is to send GitHub data to Slack
                cross_platform_result = await handle_cross_platform_action(github_result, intent, slack_mcp_url)
                return ChatResponse(
                    response=cross_platform_result["response"],
                    action_taken=cross_platform_result["action_taken"]
                )
            else:
                # Handle each part separately and combine the results
                slack_result = await handle_slack_request(intent, slack_mcp_url)
                combined_response = f"{github_result['response']}\n\n{slack_result['response']}"
                return ChatResponse(
                    response=combined_response,
                    action_taken={
                        "github": github_result["action_taken"],
                        "slack": slack_result["action_taken"]
                    }
                )
        
        # Handle other platform combinations as needed
        else:
            return ChatResponse(
                response="I'm not sure what you're asking for. Could you please clarify if you need help with GitHub, Slack, Jira, or a combination?",
                action_taken=None
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            action_taken=None
        )

async def get_jira_config(jira_mcp_url: str) -> Optional[Dict]:
    """Get Jira configuration from the MCP server"""
    try:
        logger.info(f"Attempting to fetch Jira config from MCP server at {jira_mcp_url}/config")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{jira_mcp_url}/config")
            if response.status_code == 200:
                config = response.json()
                logger.info("Successfully retrieved Jira configuration from MCP server")
                return config
            else:
                logger.error(f"Failed to get Jira configuration: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error getting Jira configuration: {str(e)}")
        return None

async def call_jira_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, jira_mcp_url: str = JIRA_MCP_BASE_URL) -> Dict:
    """Call Jira API endpoint through the MCP server"""
    try:
        logger.info(f"Calling Jira MCP server: {jira_mcp_url}")
        
        async with httpx.AsyncClient() as client:
            url = f"{jira_mcp_url}{endpoint}"
            logger.info(f"Calling Jira MCP endpoint: {url}")
            
            if method == "GET":
                response = await client.get(url, params=data)
            elif method == "POST":
                response = await client.post(url, json=data)
            elif method == "PUT":
                response = await client.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                logger.error(f"Jira MCP error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Jira MCP error: {response.text}")
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Error calling Jira MCP API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling Jira MCP: {str(e)}")

async def handle_jira_request(params: Dict, jira_mcp_url: str) -> Dict:
    """Handle Jira-related requests"""
    action = params.get("jira_action")
    project_key = params.get("project_key")
    ticket_id = params.get("ticket_id")
    
    # Check if Jira is configured
    config = await get_jira_config(jira_mcp_url)
    if not config:
        return {
            "response": "To use Jira functionality, you need to configure Jira first. Please configure it in the settings.",
            "action_taken": None
        }
    
    # Handle list_projects action
    if action == "list_projects":
        try:
            result = await call_jira_api("/projects", jira_mcp_url=jira_mcp_url)
            
            projects = result.get("projects", [])
            if not projects:
                return {
                    "response": "No projects found in your Jira instance.",
                    "action_taken": {"action": "list_projects", "result": []}
                }
            
            # Format the project list for display
            projects_list = "\n".join([
                f"• {project.get('name', 'Unknown')} ({project.get('key', 'Unknown')}) - {project.get('projectTypeKey', 'Unknown')} project"
                for project in projects
            ])
            
            return {
                "response": f"Here are the projects in your Jira instance:\n\n{projects_list}",
                "action_taken": {"action": "list_projects", "result": projects}
            }
        except Exception as e:
            logger.error(f"Error listing Jira projects: {str(e)}")
            return {
                "response": f"Error listing Jira projects: {str(e)}",
                "action_taken": None
            }
    
    # Handle list_tickets action
    elif action == "list_tickets":
        if not project_key:
            return {
                "response": "I need a project key to list tickets. Please provide one.",
                "action_taken": None
            }
        
        try:
            query_params = {"project_key": project_key}
            
            # Add optional filters if provided
            status = params.get("status")
            assignee = params.get("assignee")
            if status:
                query_params["status"] = status
            if assignee:
                query_params["assignee"] = assignee
            
            result = await call_jira_api("/tickets", method="GET", data=query_params, jira_mcp_url=jira_mcp_url)
            
            tickets = result.get("tickets", [])
            if not tickets:
                return {
                    "response": f"No tickets found for project {project_key}.",
                    "action_taken": {"action": "list_tickets", "result": []}
                }
            
            # Format the ticket list for display
            tickets_list = "\n".join([
                f"• {ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}\n"
                f"  Status: {ticket.get('status', 'Unknown')} | Priority: {ticket.get('priority', 'Unknown')} | Assignee: {ticket.get('assignee', 'Unassigned')}"
                for ticket in tickets[:10]  # Limit to 10 tickets for readability
            ])
            
            total = result.get("total", 0)
            if total > 10:
                tickets_list += f"\n\n...and {total - 10} more tickets."
            
            return {
                "response": f"Here are the tickets for project {project_key}:\n\n{tickets_list}",
                "action_taken": {"action": "list_tickets", "result": tickets}
            }
        except Exception as e:
            logger.error(f"Error listing Jira tickets: {str(e)}")
            return {
                "response": f"Error listing Jira tickets: {str(e)}",
                "action_taken": None
            }
    
    # Handle get_ticket action
    elif action == "get_ticket":
        if not ticket_id:
            return {
                "response": "I need a ticket ID to get details. Please provide one.",
                "action_taken": None
            }
        
        try:
            result = await call_jira_api(f"/ticket/{ticket_id}", jira_mcp_url=jira_mcp_url)
            
            ticket = result.get("ticket", {})
            if not ticket:
                return {
                    "response": f"Ticket {ticket_id} not found.",
                    "action_taken": {"action": "get_ticket", "result": None}
                }
            
            # Format the ticket details for display
            ticket_details = (
                f"**{ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}**\n\n"
                f"**Project**: {ticket.get('project', 'Unknown')}\n"
                f"**Status**: {ticket.get('status', 'Unknown')}\n"
                f"**Type**: {ticket.get('issue_type', 'Unknown')}\n"
                f"**Priority**: {ticket.get('priority', 'Unknown')}\n"
                f"**Assignee**: {ticket.get('assignee', 'Unassigned')}\n"
                f"**Reporter**: {ticket.get('reporter', 'Unknown')}\n"
                f"**Created**: {ticket.get('created', 'Unknown')}\n"
                f"**Updated**: {ticket.get('updated', 'Unknown')}\n\n"
                f"**Description**:\n{ticket.get('description', 'No description')}"
            )
            
            return {
                "response": f"Here are the details for ticket {ticket_id}:\n\n{ticket_details}",
                "action_taken": {"action": "get_ticket", "result": ticket}
            }
        except Exception as e:
            logger.error(f"Error getting Jira ticket: {str(e)}")
            return {
                "response": f"Error getting Jira ticket details: {str(e)}",
                "action_taken": None
            }
    
    # Handle create_ticket action
    elif action == "create_ticket":
        if not project_key:
            return {
                "response": "I need a project key to create a ticket. Please provide one.",
                "action_taken": None
            }
        
        summary = params.get("summary")
        if not summary:
            return {
                "response": "I need a summary to create a ticket. Please provide one.",
                "action_taken": None
            }
        
        try:
            ticket_data = {
                "summary": summary,
                "project_key": project_key,
                "issue_type": params.get("issue_type", "Task")
            }
            
            # Add optional fields if provided
            description = params.get("description")
            priority = params.get("priority")
            assignee = params.get("assignee")
            labels = params.get("labels")
            
            if description:
                ticket_data["description"] = description
            if priority:
                ticket_data["priority"] = priority
            if assignee:
                ticket_data["assignee"] = assignee
            if labels:
                ticket_data["labels"] = labels if isinstance(labels, list) else [labels]
            
            result = await call_jira_api("/ticket/create", method="POST", data=ticket_data, jira_mcp_url=jira_mcp_url)
            
            ticket_key = result.get("key")
            if not ticket_key:
                return {
                    "response": "Ticket created successfully, but unable to retrieve its key.",
                    "action_taken": {"action": "create_ticket", "result": result}
                }
            
            ticket = result.get("ticket", {})
            
            return {
                "response": f"Ticket {ticket_key} created successfully:\n\n"
                          f"**{ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}**\n"
                          f"**Status**: {ticket.get('status', 'Unknown')} | **Priority**: {ticket.get('priority', 'Unknown')} | **Assignee**: {ticket.get('assignee', 'Unassigned')}",
                "action_taken": {"action": "create_ticket", "result": ticket}
            }
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {str(e)}")
            return {
                "response": f"Error creating Jira ticket: {str(e)}",
                "action_taken": None
            }
    
    # Handle update_ticket action
    elif action == "update_ticket":
        if not ticket_id:
            return {
                "response": "I need a ticket ID to update. Please provide one.",
                "action_taken": None
            }
        
        try:
            update_data = {}
            
            # Add fields that should be updated
            summary = params.get("summary")
            description = params.get("description")
            status = params.get("status")
            priority = params.get("priority")
            assignee = params.get("assignee")
            labels = params.get("labels")
            
            if summary:
                update_data["summary"] = summary
            if description:
                update_data["description"] = description
            if status:
                update_data["status"] = status
            if priority:
                update_data["priority"] = priority
            if assignee:
                update_data["assignee"] = assignee
            if labels:
                update_data["labels"] = labels if isinstance(labels, list) else [labels]
            
            if not update_data:
                return {
                    "response": "I need at least one field to update. Please provide summary, description, status, priority, assignee, or labels.",
                    "action_taken": None
                }
            
            result = await call_jira_api(f"/ticket/{ticket_id}", method="PUT", data=update_data, jira_mcp_url=jira_mcp_url)
            
            ticket = result.get("ticket", {})
            
            return {
                "response": f"Ticket {ticket_id} updated successfully:\n\n"
                          f"**{ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}**\n"
                          f"**Status**: {ticket.get('status', 'Unknown')} | **Priority**: {ticket.get('priority', 'Unknown')} | **Assignee**: {ticket.get('assignee', 'Unassigned')}",
                "action_taken": {"action": "update_ticket", "result": ticket}
            }
        except Exception as e:
            logger.error(f"Error updating Jira ticket: {str(e)}")
            return {
                "response": f"Error updating Jira ticket: {str(e)}",
                "action_taken": None
            }
    
    else:
        return {
            "response": f"I understand you want to perform a Jira action ({action}), but I need more information to proceed.",
            "action_taken": None
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)