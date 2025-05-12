from state import State
from groq import Groq
import httpx
import os
from typing import Optional, Dict
from pydantic import BaseModel
import logging
from agentdock.chatbot.app import call_slack_api
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def supervisorNode(state: State):
  groq_api_key = "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"
  client = Groq(api_key=groq_api_key)
  completion = client.chat.completions.create(
      model="llama3-8b-8192",
      messages=[
          {"role": "system", "content": f"You are a supervisor agent, 
           you will look at the user input and decide which of the 3 nodes(Github Agent, Slack Agent and Jira Agent) to call.
           If multiple agents are to be called, return them in that order
           Instructions:
           Return GITHUB if Github Agent is to be called. Return SLACK if slack agent is to be called and return JIRA if Jira Agent is to be called.
           If multiple agents have to be called, return them seperated by spaces, for example, if Github and then Slack is to be called,
           return GITHUB SLACK
           "},
          {"role": "user", "content": state['user_message']}
      ],
      temperature=0.1,
      max_tokens=300,
      response_format={"type": "json_object"}
  )
  response = completion.choices[0].message.content.strip()
  if 'GITHUB' in response or 'SLACK' in response or 'JIRA' in response:
    state['response'] = response
    return state
  

class CreatePRRequest(BaseModel):
    title: str
    body: str
    head: str
    base: str = "main"
async def githubNode(state: State):
  groq_api_key = "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"
  client = Groq(api_key=groq_api_key)
  prompt = f"""
        You are an intent classifier for a chatbot that handles operations. 
        Analyze this message: "{state['user_message']}"
        
        Return a JSON object with the following fields:
        - github_action: one of [list_prs, get_pr_summary, get_stats, create_pr, list_my_repos]
        - owner: repository owner (if mentioned)
        - repo: repository name (if mentioned)
        - pr_number: pull request number (if mentioned)
        - pr_title: pull request title (if mentioned)
        - pr_body: pull request body (if mentioned)
        - pr_head: pull request head (if mentioned)
        - pr_base: pull request base branch (if mentioned)
        
        Return ONLY the JSON object, no other text.
        """
  completion = client.chat.completions.create(
      model="llama3-8b-8192",
      messages=[
          {"role": "system", "content": f"You are an intent classifier for GitHub operations. Always return valid JSON."},
          {"role": "user", "content": prompt}
      ],
      temperature=0.1,
      max_tokens=300,
      response_format={"type": "json_object"}
  )
  response = completion.choices[0].message.content.strip()
  action = response.get("github_action")
  owner = response.get("owner")
  repo = response.get("repo")
  pr_number = response.get("pr_number")
  pr_title = response.get("pr_title")
  pr_body = response.get("pr_body")
  pr_head = response.get("pr_head")
  pr_base = response.get("pr_base")
  github_mcp_url = os.getenv("GITHUB_MCP_URL", "http://localhost:8001")
  
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
                  return state
          
          # Format response with repository details
              state["chat_answer"].append({
                  "response": "Here are your repositories:\n" + "\n".join([
                      f"• {r['name']} ({'Private' if r['private'] else 'Public'}) - {r['description']}\n"
                      f"  Stars: {r['stars']}, Forks: {r['forks']}\n"
                      f"  URL: {r['url']}"
                      for r in repos
                  ]),
                  "action_taken": {"action": "list_my_repos", "result": repos}
              })
      except Exception as e:
          # Catch-all for any other unexpected errors
          print(f"Unexpected error listing repositories: {str(e)}")
          state["chat_answer"].append({
              "response": "To access your repositories, you need to configure GitHub first. Please use:\n\n"
                      "POST http://localhost:8001/configure\n"
                      "Content-Type: application/json\n"
                      '{"token": "your_github_token"}',
              "action_taken": None
          })
  
  # Map actions to GitHub API endpoints
  if action == "list_prs":
      # result = await call_github_api(f"repos/{owner}/{repo}/pulls", use_token=not is_public)
      async with httpx.AsyncClient() as client:
          # First try to get the configuration
          response = await client.get(f"{github_mcp_url}/{owner}/{repo}/prs")
          response.raise_for_status()
          result = response.json()
          if not result:
              state["chat_answer"].append({
                  "response": f"No open pull requests found for {owner}/{repo}.",
                  "action_taken": {"action": "list_prs", "result": []}
              })
      
          pr_list = "\n".join([
              f"• #{pr['number']} - {pr['title']} by {pr['user']['login']}\n"
              f"  Status: {pr['state']}, Created: {pr['created_at']}\n"
              f"  URL: {pr['html_url']}"
              for pr in result
          ])
      
          state["chat_answer"].append({
              "response": f"Here are the pull requests for {owner}/{repo}:\n\n{pr_list}",
              "action_taken": {"action": "list_prs", "result": result},
              "raw_data": result  # Store the raw data for potential cross-platform actions
          })
      
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
      
          state["chat_answer"].append({
              "response": f"Here's the summary of PR #{pr_number} in {owner}/{repo}:\n\n{pr_summary}",
              "action_taken": {"action": "get_pr_summary", "result": result},
              "raw_data": result  # Store the raw data for potential cross-platform actions
          })
          
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
      
          state["chat_answer"].append({
              "response": f"Here are the statistics for {owner}/{repo}:\n\n{repo_stats}",
              "action_taken": {"action": "get_stats", "result": result}
          })
      
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
      
      state["chat_answer"].append({
          "response": f"PR created",
          "action_taken": {"action": "get_repo_info", "result": result}
      })
      
  else:
      state["chat_answer"].append({
          "response": f"I understand you want to {action} for {owner}/{repo}, but I need more information to proceed.",
          "action_taken": None
      })

async def slackNode(state: State):
  groq_api_key = "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"
  client = Groq(api_key=groq_api_key)
  prompt = f"""
        You are an intent classifier for a chatbot that handles Slack operations. 
        Analyze this message: "{state['user_message']}"
        
        Return a JSON object with the following fields:
        - slack_action: one of [list_channels, send_message, get_conversation_history]
        - channel: channel name or ID (if mentioned)
        - message_content: content of message to send (if applicable)
        - time_range: time range for history (if applicable)
        
        Return ONLY the JSON object, no other text.
        """
  completion = client.chat.completions.create(
      model="llama3-8b-8192",
      messages=[
          {"role": "system", "content": f"You are an intent classifier for Slack operations. Always return valid JSON."},
          {"role": "user", "content": prompt}
      ],
      temperature=0.1,
      max_tokens=300,
      response_format={"type": "json_object"}
  )
  response = completion.choices[0].message.content.strip()
  action = response.get("slack_action")
  channel = response.get("channel")
  message_content = response.get("message_content")
  time_range = response.get("time_range")
  slack_mcp_url = os.getenv("SLACK_MCP_URL", "http://localhost:8003")
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
              state["chat_answer"].append({
                  "response": "No channels found in your Slack workspace.",
                  "action_taken": {"action": "list_channels", "result": []}
              })
          
          # Format the channel list for display
          channels_list = "\n".join([
              f"• #{channel.get('name', 'unknown')} ({channel.get('id', 'unknown')}) - {'Private' if channel.get('is_private', False) else 'Public'}"
              for channel in channels
          ])
          
          state["chat_answer"].append({
              "response": f"Here are the channels in your Slack workspace:\n\n{channels_list}",
              "action_taken": {"action": "list_channels", "result": channels}
          })
      except Exception as e:
          logger.error(f"Error listing Slack channels: {str(e)}")
          return {
              "response": f"Error listing Slack channels: {str(e)}",
              "action_taken": None
          }
  
  # Handle send_message action
  elif action == "send_message":
      if not channel:
          state["chat_answer"].append({
              "response": "I need a channel name or ID to send a message.",
              "action_taken": None
          })
      
      if not message_content:
          state["chat_answer"].append({
              "response": "I need message content to send to the Slack channel.",
              "action_taken": None
          })
      
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
          
          state["chat_answer"].append({
              "response": f"Message successfully sent to {channel}!",
              "action_taken": {"action": "send_message", "channel": channel, "result": result}
          })
      except Exception as e:
          logger.error(f"Error sending Slack message: {str(e)}")
          return {
              "response": f"Error sending message to Slack: {str(e)}",
              "action_taken": None
          }
  
  # Handle get_conversation_history action
  elif action == "get_conversation_history":
      if not channel:
          state["chat_answer"].append({
              "response": "I need a channel name or ID to get conversation history.",
              "action_taken": None
          })
      
      try:
          params = {"channel": channel, "limit": 10}
          if time_range:
              # Process time_range if provided
              pass
              
          result = await call_slack_api("conversations.history", method="GET", data=params)
          
          messages = result.get("messages", [])
          if not messages:
              state["chat_answer"].append({
                  "response": f"No messages found in {channel}.",
                  "action_taken": {"action": "get_conversation_history", "result": []}
              })
          
          # Format the conversation history
          messages_list = "\n\n".join([
              f"*{msg.get('user', 'Unknown')} at {msg.get('ts', 'Unknown time')}:*\n{msg.get('text', 'No text')}"
              for msg in messages
          ])
          
          state["chat_answer"].append({
              "response": f"Here are the recent messages in {channel}:\n\n{messages_list}",
              "action_taken": {"action": "get_conversation_history", "result": messages}
          })
      except Exception as e:
          logger.error(f"Error getting Slack conversation history: {str(e)}")
          state["chat_answer"].append({
              "response": f"Error getting Slack conversation history: {str(e)}",
              "action_taken": None
          })
  
  else:
      state["chat_answer"].append({
          "response": f"I understand you want to perform a Slack action, but I need more information to proceed.",
          "action_taken": None
      })

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

async def call_jira_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None, jira_mcp_url: str = os.getenv("JIRA_MCP_URL", "http://localhost:8004") ) -> Dict:
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
                # raise HTTPException(status_code=response.status_code, detail=f"Jira MCP error: {response.text}")
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Error calling Jira MCP API: {str(e)}")
        # raise HTTPException(status_code=500, detail=f"Error calling Jira MCP: {str(e)}")

async def jiraNode(state: State):
  groq_api_key = "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"
  client = Groq(api_key=groq_api_key)
  prompt = f"""
        You are an intent classifier for a chatbot that handles Jira operations. 
        Analyze this message: "{state['user_message']}"
        
        Return a JSON object with the following fields:
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
  completion = client.chat.completions.create(
      model="llama3-8b-8192",
      messages=[
          {"role": "system", "content": f"You are an intent classifier for Jira operations. Always return valid JSON."},
          {"role": "user", "content": prompt}
      ],
      temperature=0.1,
      max_tokens=300,
      response_format={"type": "json_object"}
  )
  response = completion.choices[0].message.content.strip()
  jira_mcp_url = os.getenv("JIRA_MCP_URL", "http://localhost:8004")
  action = response.get("jira_action")
  project_key = response.get("project_key")
  ticket_id = response.get("ticket_id")
  
  # Check if Jira is configured
  config = await get_jira_config(jira_mcp_url)
  if not config:
      state["chat_answer"].append({
          "response": "To use Jira functionality, you need to configure Jira first. Please configure it in the settings.",
          "action_taken": None
      })
  
  # Handle list_projects action
  if action == "list_projects":
      try:
          result = await call_jira_api("/projects", jira_mcp_url=jira_mcp_url)
          
          projects = result.get("projects", [])
          if not projects:
              state["chat_answer"].append({
                  "response": "No projects found in your Jira instance.",
                  "action_taken": {"action": "list_projects", "result": []}
              })
          
          # Format the project list for display
          projects_list = "\n".join([
              f"• {project.get('name', 'Unknown')} ({project.get('key', 'Unknown')}) - {project.get('projectTypeKey', 'Unknown')} project"
              for project in projects
          ])
          
          state["chat_answer"].append({
              "response": f"Here are the projects in your Jira instance:\n\n{projects_list}",
              "action_taken": {"action": "list_projects", "result": projects}
          })
      except Exception as e:
          logger.error(f"Error listing Jira projects: {str(e)}")
          state["chat_answer"].append({
              "response": f"Error listing Jira projects: {str(e)}",
              "action_taken": None
          })
  
  # Handle list_tickets action
  elif action == "list_tickets":
      if not project_key:
          state["chat_answer"].append({
              "response": "I need a project key to list tickets. Please provide one.",
              "action_taken": None
          })
      
      try:
          query_params = {"project_key": project_key}
          
          # Add optional filters if provided
          status = response.get("status")
          assignee = response.get("assignee")
          if status:
              query_params["status"] = status
          if assignee:
              query_params["assignee"] = assignee
          
          result = await call_jira_api("/tickets", method="GET", data=query_params, jira_mcp_url=jira_mcp_url)
          
          tickets = result.get("tickets", [])
          if not tickets:
              state["chat_answer"].append({
                  "response": f"No tickets found for project {project_key}.",
                  "action_taken": {"action": "list_tickets", "result": []}
              })
          
          # Format the ticket list for display
          tickets_list = "\n".join([
              f"• {ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}\n"
              f"  Status: {ticket.get('status', 'Unknown')} | Priority: {ticket.get('priority', 'Unknown')} | Assignee: {ticket.get('assignee', 'Unassigned')}"
              for ticket in tickets[:10]  # Limit to 10 tickets for readability
          ])
          
          total = result.get("total", 0)
          if total > 10:
              tickets_list += f"\n\n...and {total - 10} more tickets."
          
          state["chat_answer"].append({
              "response": f"Here are the tickets for project {project_key}:\n\n{tickets_list}",
              "action_taken": {"action": "list_tickets", "result": tickets}
          })
      except Exception as e:
          logger.error(f"Error listing Jira tickets: {str(e)}")
          state["chat_answer"].append({
              "response": f"Error listing Jira tickets: {str(e)}",
              "action_taken": None
          })
  
  # Handle get_ticket action
  elif action == "get_ticket":
      if not ticket_id:
          state["chat_answer"].append({
              "response": "I need a ticket ID to get details. Please provide one.",
              "action_taken": None
          })
      
      try:
          result = await call_jira_api(f"/ticket/{ticket_id}", jira_mcp_url=jira_mcp_url)
          
          ticket = result.get("ticket", {})
          if not ticket:
              state["chat_answer"].append({
                  "response": f"Ticket {ticket_id} not found.",
                  "action_taken": {"action": "get_ticket", "result": None}
              })
          
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
          
          state["chat_answer"].append({
              "response": f"Here are the details for ticket {ticket_id}:\n\n{ticket_details}",
              "action_taken": {"action": "get_ticket", "result": ticket}
          })
      except Exception as e:
          logger.error(f"Error getting Jira ticket: {str(e)}")
          state["chat_answer"].append({
              "response": f"Error getting Jira ticket details: {str(e)}",
              "action_taken": None
          })
  
  # Handle create_ticket action
  elif action == "create_ticket":
      if not project_key:
          state["chat_answer"].append({
              "response": "I need a project key to create a ticket. Please provide one.",
              "action_taken": None
          })
      
      summary = response.get("summary")
      if not summary:
          state["chat_answer"].append({
              "response": "I need a summary to create a ticket. Please provide one.",
              "action_taken": None
          })
      
      try:
          ticket_data = {
              "summary": summary,
              "project_key": project_key,
              "issue_type": response.get("issue_type", "Task")
          }
          
          # Add optional fields if provided
          description = response.get("description")
          priority = response.get("priority")
          assignee = response.get("assignee")
          labels = response.get("labels")
          
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
              state["chat_answer"].append({
                  "response": "Ticket created successfully, but unable to retrieve its key.",
                  "action_taken": {"action": "create_ticket", "result": result}
              })
          
          ticket = result.get("ticket", {})
          
          state["chat_answer"].append({
              "response": f"Ticket {ticket_key} created successfully:\n\n"
                        f"**{ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}**\n"
                        f"**Status**: {ticket.get('status', 'Unknown')} | **Priority**: {ticket.get('priority', 'Unknown')} | **Assignee**: {ticket.get('assignee', 'Unassigned')}",
              "action_taken": {"action": "create_ticket", "result": ticket}
          })
      except Exception as e:
          logger.error(f"Error creating Jira ticket: {str(e)}")
          state["chat_answer"].append({
              "response": f"Error creating Jira ticket: {str(e)}",
              "action_taken": None
          })
  
  # Handle update_ticket action
  elif action == "update_ticket":
      if not ticket_id:
          state["chat_answer"].append({
              "response": "I need a ticket ID to update. Please provide one.",
              "action_taken": None
          })
      
      try:
          update_data = {}
          
          # Add fields that should be updated
          summary = response.get("summary")
          description = response.get("description")
          status = response.get("status")
          priority = response.get("priority")
          assignee = response.get("assignee")
          labels = response.get("labels")
          
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
              state["chat_answer"].append({
                  "response": "I need at least one field to update. Please provide summary, description, status, priority, assignee, or labels.",
                  "action_taken": None
              })
          
          result = await call_jira_api(f"/ticket/{ticket_id}", method="PUT", data=update_data, jira_mcp_url=jira_mcp_url)
          
          ticket = result.get("ticket", {})
          
          state["chat_answer"].append({
              "response": f"Ticket {ticket_id} updated successfully:\n\n"
                        f"**{ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')}**\n"
                        f"**Status**: {ticket.get('status', 'Unknown')} | **Priority**: {ticket.get('priority', 'Unknown')} | **Assignee**: {ticket.get('assignee', 'Unassigned')}",
              "action_taken": {"action": "update_ticket", "result": ticket}
          })
      except Exception as e:
          logger.error(f"Error updating Jira ticket: {str(e)}")
          state["chat_answer"].append({
              "response": f"Error updating Jira ticket: {str(e)}",
              "action_taken": None
          })
  
  else:
      state["chat_answer"].append({
          "response": f"I understand you want to perform a Jira action ({action}), but I need more information to proceed.",
          "action_taken": None
      })

def finalNode(state: State):
    all_responses = "\n\n".join(msg["response"] for msg in state["chat_answer"])

    all_actions = [
        msg["action_taken"]
        for msg in state.get("chat_answer", [])
        if msg.get("action_taken") is not None
    ]

    state['final_answer'] = {
        "response": all_responses,
        "action_taken": all_actions or None
    }

    # # Collect all actions taken (if any exist)
    # state["action_taken"] = [
    #     msg["action_taken"]
    #     for msg in state["user_message"]
    #     if msg.get("action_taken") is not None
    # ] or None  # Optional: set to None if empty

    return state