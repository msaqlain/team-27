import React, { useEffect, useState } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle, TextField, Button, Typography, Alert } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import config from '../config';

// LocalStorage keys
const GH_TOKEN_KEY = 'github_token';
const GH_MCP_URL_KEY = 'github_mcp_url';
const GH_CONFIG_STATUS_KEY = 'github_config_status';

/**
 * A reusable modal component for GitHub token configuration
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the modal is open
 * @param {Function} props.onClose - Function to call when the modal is closed
 * @returns {JSX.Element} The GitHubTokenModal component
 */
const GitHubTokenModal = ({ open, onClose }) => {
  const [githubToken, setGithubToken] = useState('');
  const [mcpServerUrl, setMcpServerUrl] = useState('http://localhost:8001');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [configStatus, setConfigStatus] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    // Load saved values from localStorage when modal opens
    if (open) {
      const savedToken = localStorage.getItem(GH_TOKEN_KEY) || '';
      const savedMcpUrl = localStorage.getItem(GH_MCP_URL_KEY) || 'http://localhost:8001';
      const savedStatus = localStorage.getItem(GH_CONFIG_STATUS_KEY) || '';
      
      setGithubToken(savedToken);
      setMcpServerUrl(savedMcpUrl);
      setConfigStatus(savedStatus);
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!githubToken.trim()) {
      enqueueSnackbar('Please enter a GitHub token', { variant: 'error' });
      return;
    }

    if (!mcpServerUrl.trim()) {
      enqueueSnackbar('Please enter an MCP Server URL', { variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      // Save values to localStorage
      localStorage.setItem(GH_TOKEN_KEY, githubToken);
      localStorage.setItem(GH_MCP_URL_KEY, mcpServerUrl);
      
      // Update the config with the new MCP URL
      config.updateGithubMcpUrl();
      
      // Call the MCP server API
      await axios.post(`${mcpServerUrl}/configure`, { token: githubToken });
      
      // Update status in localStorage
      const timestamp = new Date().toLocaleString();
      const status = `Configured successfully at ${timestamp}`;
      localStorage.setItem(GH_CONFIG_STATUS_KEY, status);
      setConfigStatus(status);
      
      enqueueSnackbar('GitHub token configured successfully', { variant: 'success' });
      onClose();
    } catch (error) {
      console.error('Error configuring GitHub token:', error);
      
      // Update status with error
      const timestamp = new Date().toLocaleString();
      const status = `Configuration failed at ${timestamp}: ${error.message}`;
      localStorage.setItem(GH_CONFIG_STATUS_KEY, status);
      setConfigStatus(status);
      
      enqueueSnackbar('Failed to configure GitHub token', { variant: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Configure GitHub Access</DialogTitle>
      <DialogContent>
        {configStatus && (
          <Alert 
            severity={configStatus.includes('failed') ? 'warning' : 'success'} 
            className="mb-4"
            sx={{ marginBottom: 2, marginTop: 1 }}
          >
            {configStatus}
          </Alert>
        )}
        
        <TextField
          margin="dense"
          label="MCP Server URL"
          type="text"
          fullWidth
          variant="outlined"
          value={mcpServerUrl}
          onChange={(e) => setMcpServerUrl(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter MCP Server URL"
          helperText="URL of the GitHub MCP Server (e.g., https://github-mcp-server.example.com)"
          sx={{ marginBottom: 2 }}
        />
        
        <TextField
          margin="dense"
          label="GitHub Token"
          type="password"
          fullWidth
          variant="outlined"
          value={githubToken}
          onChange={(e) => setGithubToken(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your GitHub personal access token"
          helperText="This token will be used to access your GitHub repositories"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} color="primary" disabled={isSubmitting}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          color="primary" 
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GitHubTokenModal; 