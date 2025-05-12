// Configuration settings for the chat application

const isDevelopment = process.env.NODE_ENV === 'development';

// Get MCP server URLs from localStorage (if available)
const getGithubMcpUrl = () => {
  if (typeof window !== 'undefined' && window.localStorage) {
    return localStorage.getItem('github_mcp_url') || (isDevelopment ? 'http://localhost:8001' : '');
  }
  return isDevelopment ? 'http://localhost:8001' : '';
};

const getSlackMcpUrl = () => {
  if (typeof window !== 'undefined' && window.localStorage) {
    return localStorage.getItem('slack_mcp_url') || (isDevelopment ? 'http://localhost:8003' : '');
  }
  return isDevelopment ? 'http://localhost:8003' : '';
};

const getJiraMcpUrl = () => {
  if (typeof window !== 'undefined' && window.localStorage) {
    return localStorage.getItem('jira_mcp_url') || (isDevelopment ? 'http://localhost:8004' : '');
  }
  return isDevelopment ? 'http://localhost:8004' : '';
};

// API endpoints
const config = {
  // Base API URL (empty for same-origin requests)
  API_BASE_URL: isDevelopment ? 'http://localhost:8002' : '',
  
  // MCP server URLs
  GITHUB_MCP_URL: getGithubMcpUrl(),
  SLACK_MCP_URL: getSlackMcpUrl(),
  JIRA_MCP_URL: getJiraMcpUrl(),
  
  // Endpoints
  ENDPOINTS: {
    CHAT: '/chat'
  },
  
  // Update the MCP URLs from localStorage (call these when URLs change)
  updateGithubMcpUrl: () => {
    if (typeof window !== 'undefined' && window.localStorage) {
      config.GITHUB_MCP_URL = localStorage.getItem('github_mcp_url') || (isDevelopment ? 'http://localhost:8001' : '');
    }
  },
  
  updateSlackMcpUrl: () => {
    if (typeof window !== 'undefined' && window.localStorage) {
      config.SLACK_MCP_URL = localStorage.getItem('slack_mcp_url') || (isDevelopment ? 'http://localhost:8003' : '');
    }
  },
  
  updateJiraMcpUrl: () => {
    if (typeof window !== 'undefined' && window.localStorage) {
      config.JIRA_MCP_URL = localStorage.getItem('jira_mcp_url') || (isDevelopment ? 'http://localhost:8004' : '');
    }
  },
  
  // Update all MCP URLs from localStorage
  updateAllMcpUrls: () => {
    config.updateGithubMcpUrl();
    config.updateSlackMcpUrl();
    config.updateJiraMcpUrl();
  }
};

export default config;