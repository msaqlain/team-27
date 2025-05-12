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
from langchain_service import LangChainService

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

# Initialize LangChain service
langchain_service = LangChainService(groq_api_key)

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[Dict] = None

# MCP Server endpoints - will be configured by Dapr
GITHUB_MCP_BASE_URL = os.getenv("GITHUB_MCP_URL", "http://localhost:8001")
SLACK_MCP_BASE_URL = os.getenv("SLACK_MCP_URL", "http://localhost:8003")
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

async def get_slack_token() -> Optional[str]:
    """Get Slack token from Slack MCP server configuration"""
    try:
        logger.info(f"Attempting to fetch Slack token from MCP server at {SLACK_MCP_BASE_URL}/config")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SLACK_MCP_BASE_URL}/config")
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

async def call_slack_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """Call Slack API endpoint"""
    try:
        token = await get_slack_token()
        if not token:
            logger.error("No Slack token available")
            raise HTTPException(
                status_code=400, 
                detail="Slack token not configured. Please configure using the MCP server first. Make sure to call POST http://localhost:8003/configure with your token."
            )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        async with httpx.AsyncClient() as client:
            url = f"https://slack.com/api/{endpoint}"
            logger.info(f"Calling Slack API endpoint: {url}")
            
            if method == "GET":
                response = await client.get(url, headers=headers, params=data)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_json = response.json()
            
            if not response_json.get("ok", False):
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Slack API error: {response.text}")
            
            return response_json
    except Exception as e:
        logger.error(f"Error calling Slack API: {str(e)}")
        raise

def determine_intent(message: str) -> Dict:
    """Determine if the message is related to GitHub, Slack, or both"""
    try:
        prompt = f"""
        You are an intent classifier for a chatbot that handles GitHub and Slack operations. 
        Analyze this message: "{message}"
        
        Return a JSON object with:
        1. "platform": Either "github", "slack", "both", or "conversation" (for general chat)
        2. "confidence": A number between 0 and 1 indicating your confidence
        
        If platform is "github" or "both", include these fields for GitHub:
        - github_action: one of [list_prs, get_pr_summary, get_stats, create_pr, list_my_repos]
        - owner: repository owner (if mentioned)
        - repo: repository name (if mentioned)
        - pr_number: pull request number (if mentioned)
        
        If platform is "slack" or "both", include these fields for Slack:
        - slack_action: one of [list_channels, send_message, get_conversation_history]
        - channel: channel name or ID (if mentioned)
        - message_content: content of message to send (if applicable)
        - time_range: time range for history (if applicable)
        - pr_title: pull request title (if mentioned)
        - pr_body: pull request body (if mentioned)
        - pr_head: pull request head (if mentioned)
        - pr_base: pull request base branch (if mentioned)
        
        Return ONLY the JSON object, no other text.
        """
        
        logger.info("Calling Groq API to determine intent...")
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an intent classifier for GitHub and Slack operations. Always return valid JSON."},
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
    token = await get_slack_token()
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
            
            channels = result.get("channels", [])
            if not channels:
                return {
                    "response": "No channels found in your Slack workspace.",
                    "action_taken": {"action": "list_channels", "result": []}
                }
            
            channels_list = "\n".join([
                f"• #{channel['name']} ({channel['id']}) - {'Private' if channel.get('is_private', False) else 'Public'}"
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
            }
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
    """Process chat message and return response with MCP analysis"""
    try:
        # Determine intent
        intent = await langchain_service.determine_intent(message.message)
        
        # Initialize analyses dictionary
        analyses = {}
        
        # Process based on intent
        if intent["platform"] in ["github", "both"]:
            # Handle GitHub request
            github_result = await handle_github_request(intent, GITHUB_MCP_BASE_URL)
            if github_result.get("raw_data"):
                analyses["GitHub"] = await langchain_service.analyze_mcp_data("GitHub", github_result["raw_data"])
            
            # If it's a cross-platform action, handle Slack part
            if intent["platform"] == "both" and intent.get("slack_action"):
                slack_result = await handle_cross_platform_action(github_result, intent, SLACK_MCP_BASE_URL)
                if slack_result.get("action_taken", {}).get("result"):
                    analyses["Slack"] = await langchain_service.analyze_mcp_data("Slack", slack_result["action_taken"]["result"])
        
        elif intent["platform"] == "slack":
            # Handle Slack request
            slack_result = await handle_slack_request(intent, SLACK_MCP_BASE_URL)
            if slack_result.get("action_taken", {}).get("result"):
                analyses["Slack"] = await langchain_service.analyze_mcp_data("Slack", slack_result["action_taken"]["result"])
        
        elif intent["platform"] in ["jira", "both"]:
            # Handle Jira request
            jira_result = await handle_jira_request(intent, JIRA_MCP_BASE_URL)
            if jira_result.get("raw_data"):
                analyses["Jira"] = await langchain_service.analyze_mcp_data("Jira", jira_result["raw_data"])
            
            # If it's a cross-platform action, handle other parts
            if intent["platform"] == "both":
                if intent.get("github_action"):
                    github_result = await handle_github_request(intent, GITHUB_MCP_BASE_URL)
                    if github_result.get("raw_data"):
                        analyses["GitHub"] = await langchain_service.analyze_mcp_data("GitHub", github_result["raw_data"])
                
                if intent.get("slack_action"):
                    slack_result = await handle_slack_request(intent, SLACK_MCP_BASE_URL)
                    if slack_result.get("action_taken", {}).get("result"):
                        analyses["Slack"] = await langchain_service.analyze_mcp_data("Slack", slack_result["action_taken"]["result"])
        
        # Generate response using LangChain
        response = await langchain_service.generate_response(message.message, analyses)
        
        return ChatResponse(
            response=response,
            action_taken={
                "intent": intent,
                "analyses": analyses
            }
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_jira_request(params: Dict, jira_mcp_url: str) -> Dict:
    """Handle Jira-related requests"""
    action = params.get("jira_action")
    project = params.get("project")
    issue_key = params.get("issue_key")
    sprint = params.get("sprint")
    
    try:
        async with httpx.AsyncClient() as client:
            if action == "list_issues":
                response = await client.get(f"{jira_mcp_url}/issues", params={"project": project})
                response.raise_for_status()
                result = response.json()
                return {
                    "response": f"Found {len(result)} issues in project {project}",
                    "raw_data": result
                }
            
            elif action == "get_issue_details" and issue_key:
                response = await client.get(f"{jira_mcp_url}/issues/{issue_key}")
                response.raise_for_status()
                result = response.json()
                return {
                    "response": f"Details for issue {issue_key}",
                    "raw_data": result
                }
            
            elif action == "get_sprint_status" and sprint:
                response = await client.get(f"{jira_mcp_url}/sprints/{sprint}/status")
                response.raise_for_status()
                result = response.json()
                return {
                    "response": f"Status for sprint {sprint}",
                    "raw_data": result
                }
            
            elif action == "get_team_velocity":
                response = await client.get(f"{jira_mcp_url}/velocity")
                response.raise_for_status()
                result = response.json()
                return {
                    "response": "Team velocity metrics",
                    "raw_data": result
                }
            
            else:
                return {
                    "response": "I need more information about which Jira action you want to perform.",
                    "raw_data": None
                }
    except Exception as e:
        logger.error(f"Error handling Jira request: {str(e)}")
        return {
            "response": f"Error handling Jira request: {str(e)}",
            "raw_data": None
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)