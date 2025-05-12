# Dockerized AgentDock Deployment

This directory contains the Docker configuration files needed to containerize the AgentDock application.

## Environment Setup

Create a `.env` file in the `deployment` directory with the following content:

```
# API Keys
GROQ_API_KEY=your_groq_api_key

# MCP Server URLs - Override these if necessary
GITHUB_MCP_URL=http://github-mcp:8001
SLACK_MCP_URL=http://slack-mcp:8003
JIRA_MCP_URL=http://jira-mcp:8004

# React app configuration - These are for browser access
REACT_APP_CHATBOT_URL=http://localhost:8002
REACT_APP_GITHUB_MCP_URL=http://localhost:8001
REACT_APP_SLACK_MCP_URL=http://localhost:8003
REACT_APP_JIRA_MCP_URL=http://localhost:8004
```

## Docker Compose Deployment

### Standard Deployment

```bash
cd deployment
docker-compose --env-file .env up -d
```

### Deployment with Explicit Dapr Sidecars

If you prefer more control over the Dapr sidecars, use the Dapr-specific compose file:

```bash
cd deployment
docker-compose -f dapr-docker-compose.yml --env-file .env up -d
```

## Service URLs

Once deployed, the services will be available at:

- Frontend: http://localhost:3000
- Chatbot Service: http://localhost:8002
- GitHub MCP Server: http://localhost:8001
- Slack MCP Server: http://localhost:8003
- Jira MCP Server: http://localhost:8004
- Zipkin Tracing: http://localhost:9411

## Configuration

### GitHub MCP Configuration

Send a POST request to http://localhost:8001/configure with:
```json
{
  "token": "your_github_token"
}
```

### Slack MCP Configuration

Send a POST request to http://localhost:8003/configure with:
```json
{
  "token": "your_slack_token"
}
```

### Jira MCP Configuration

Send a POST request to http://localhost:8004/configure with:
```json
{
  "token": "your_jira_token",
  "email": "your_jira_email",
  "url": "your_jira_url"
}
```

## Troubleshooting

- **Connectivity Issues**: Ensure Docker network is properly configured
- **Dapr Errors**: Check Zipkin at http://localhost:9411 for tracing information
- **Logs**: Use `docker-compose logs [service]` to view logs for a specific service 