## Prerequisites
- Python 3.10 (recommended)
- pip package manager
- OpenAI API key
- Dapr CLI and Docker installed

## Environment Setup

```bash
# Create a virtual environment
python3.10 -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

dapr init 

dapr run -f dapr.yaml

```

## Application Architecture

The application uses a microservices architecture with the following components:

### Frontend
- URL: http://localhost:3000/
- A React-based user interface for interacting with the chatbot

### Chatbot Service
- URL: http://localhost:8002/
- Processes user inputs and generates responses
- Integrates with external services via MCP servers

### MCP Servers (Microservice Communication Providers)
These servers act as intermediaries between the chatbot and external services:

1. **GitHub MCP Server**
   - URL: http://localhost:8001/
   - Endpoints:
     - `/configure` - Configure GitHub token
     - `/config` - Get current configuration
     - `/repos/{owner}/{repo}/issues` - List repository issues
     - `/search/repositories` - Search repositories
     - `/repos/{owner}/{repo}/pulls` - List pull requests

2. **Slack MCP Server**
   - URL: http://localhost:8003/
   - Endpoints:
     - `/configure` - Configure Slack token
     - `/channels/list` - List available Slack channels
     - `/chat/post` - Post messages to Slack

3. **Jira MCP Server**
   - URL: http://localhost:8004/
   - Endpoints:
     - `/configure` - Configure Jira credentials
     - `/projects` - List Jira projects
     - `/issues` - Search for issues
     - `/issues/create` - Create a new issue
     - `/issues/{issue_key}` - Get issue details
     - `/issues/{issue_key}/update` - Update an issue

All MCP servers use token-based authentication and store credentials locally. In the frontend, MCP server URLs can be configured in the settings panel, with values stored in localStorage.

## Running the Application

After starting the application with `dapr run -f dapr.yaml`, all services including the MCP servers will be available at their respective endpoints.

For debugging purposes, a "Show Logs" button is available in the settings panel, which opens Zipkin logs in a new window.

## Docker Deployment

The application can be deployed using Docker containers for all services.

### Prerequisites
- Docker and Docker Compose

### Deployment Steps

1. Navigate to the deployment directory:
   ```bash
   cd deployment
   ```

2. Create a `.env` file with your configuration:
   ```
   # API Keys
   GROQ_API_KEY=your_groq_api_key
   
   # MCP Server URLs (for internal service communication)
   GITHUB_MCP_URL=http://github-mcp:8001
   SLACK_MCP_URL=http://slack-mcp:8003
   JIRA_MCP_URL=http://jira-mcp:8004
   ```

3. Start the application with Docker Compose:
   ```bash
   docker-compose --env-file .env up -d
   ```

4. Access the application at http://localhost:3000

### Docker Services

The Docker deployment includes the following containers:
- Frontend container (React app)
- Chatbot service
- GitHub, Slack, and Jira MCP servers
- Redis for Dapr state management
- Zipkin for tracing
- Dapr sidecars for each service

For more detailed deployment instructions and troubleshooting, see the [deployment directory README](deployment/README.md).



