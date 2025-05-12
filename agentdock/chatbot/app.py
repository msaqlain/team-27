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
logger.info(f"GitHub MCP URL: {GITHUB_MCP_BASE_URL}")
logger.info(f"Slack MCP URL: {SLACK_MCP_BASE_URL}")

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
        - github_action: one of [list_prs, get_pr_summary, get_stats, get_repo_info, list_my_repos]
        - owner: repository owner (if mentioned)
        - repo: repository name (if mentioned)
        - pr_number: pull request number (if mentioned)
        
        If platform is "slack" or "both", include these fields for Slack:
        - slack_action: one of [list_channels, send_message, get_conversation_history]
        - channel: channel name or ID (if mentioned)
        - message_content: content of message to send (if applicable)
        - time_range: time range for history (if applicable)
        
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

async def handle_github_request(params: Dict) -> Dict:
    """Handle GitHub-related requests"""
    action = params.get("github_action")
    owner = params.get("owner")
    repo = params.get("repo")
    pr_number = params.get("pr_number")
    
    # Handle list_my_repos action
    if action == "list_my_repos":
        try:
            # Get user's repositories
            result = await call_github_api("user/repos", use_token=True)
            
            # Format the response
            repos = []
            for repo_data in result:
                repos.append({
                    "name": repo_data["name"],
                    "description": repo_data["description"],
                    "url": repo_data["html_url"],
                    "private": repo_data["private"],
                    "stars": repo_data["stargazers_count"],
                    "forks": repo_data["forks_count"]
                })
            
            if not repos:
                return {
                    "response": "You don't have any repositories yet.",
                    "action_taken": {"action": "list_my_repos", "result": []}
                }
            
            return {
                "response": f"Here are your repositories:\n" + "\n".join([
                    f"• {r['name']} ({'Private' if r['private'] else 'Public'}) - {r['description'] or 'No description'}\n"
                    f"  Stars: {r['stars']}, Forks: {r['forks']}\n"
                    f"  URL: {r['url']}"
                    for r in repos
                ]),
                "action_taken": {"action": "list_my_repos", "result": repos}
            }
        except Exception as e:
            logger.error(f"Error listing repositories: {str(e)}")
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
        result = await call_github_api(f"repos/{owner}/{repo}/pulls", use_token=not is_public)
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
        result = await call_github_api(f"repos/{owner}/{repo}/pulls/{pr_number}", use_token=not is_public)
        
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
        result = await call_github_api(f"repos/{owner}/{repo}", use_token=not is_public)
        
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
        
    elif action == "get_repo_info":
        result = await call_github_api(f"repos/{owner}/{repo}", use_token=not is_public)
        
        # Format repo info
        repo_info = (
            f"Repository: {result['full_name']}\n"
            f"Description: {result['description'] or 'No description'}\n"
            f"Language: {result.get('language', 'Not specified')}\n"
            f"Visibility: {'Private' if result.get('private', True) else 'Public'}\n"
            f"Stars: {result['stargazers_count']}\n"
            f"Forks: {result['forks_count']}\n"
            f"URL: {result['html_url']}"
        )
        
        return {
            "response": f"Here's information about {owner}/{repo}:\n\n{repo_info}",
            "action_taken": {"action": "get_repo_info", "result": result}
        }
        
    else:
        return {
            "response": f"I understand you want to {action} for {owner}/{repo}, but I need more information to proceed.",
            "action_taken": None
        }

async def handle_slack_request(params: Dict) -> Dict:
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

async def handle_cross_platform_action(github_result: Dict, slack_params: Dict) -> Dict:
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
    """Process natural language message and interact with GitHub and/or Slack"""
    try:
        logger.info(f"Received chat message: {message.message}")
        
        # Determine intent (GitHub, Slack, or both)
        intent = determine_intent(message.message)
        platform = intent.get("platform", "conversation")
        
        logger.info(f"Determined platform: {platform}")
        
        # Handle general conversation
        if platform == "conversation":
            return ChatResponse(
                response="Hello! I'm your assistant. I can help you with:\n"
                        "• GitHub: View repositories, check pull requests, get repository statistics\n"
                        "• Slack: List channels, send messages, get conversation history\n"
                        "• Cross-platform: Send GitHub information to Slack channels\n\n"
                        "Just let me know what you'd like to do!",
                action_taken={"action": "conversation"}
            )
        
        # Handle GitHub-only requests
        elif platform == "github":
            result = await handle_github_request(intent)
            return ChatResponse(
                response=result["response"],
                action_taken=result["action_taken"]
            )
        
        # Handle Slack-only requests
        elif platform == "slack":
            result = await handle_slack_request(intent)
            return ChatResponse(
                response=result["response"],
                action_taken=result["action_taken"]
            )
        
        # Handle cross-platform requests (both GitHub and Slack)
        elif platform == "both":
            # First handle the GitHub part
            github_result = await handle_github_request(intent)
            
            # Then handle the Slack part
            if "slack_action" in intent and intent["slack_action"] == "send_message":
                # If the intent is to send GitHub data to Slack
                cross_platform_result = await handle_cross_platform_action(github_result, intent)
                return ChatResponse(
                    response=cross_platform_result["response"],
                    action_taken=cross_platform_result["action_taken"]
                )
            else:
                # Handle each part separately and combine the results
                slack_result = await handle_slack_request(intent)
                combined_response = f"{github_result['response']}\n\n{slack_result['response']}"
                return ChatResponse(
                    response=combined_response,
                    action_taken={
                        "github": github_result["action_taken"],
                        "slack": slack_result["action_taken"]
                    }
                )
        
        else:
            return ChatResponse(
                response="I'm not sure what you're asking for. Could you please clarify if you need help with GitHub, Slack, or both?",
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