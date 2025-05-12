// Configuration settings for the chat application

const isDevelopment = process.env.NODE_ENV === 'development';

// API endpoints
const config = {
  // Base API URL (empty for same-origin requests)
  API_BASE_URL: isDevelopment ? 'http://localhost:8002' : '',
  
  // Endpoints
  ENDPOINTS: {
    CHAT: '/chat'
  }
};

export default config;