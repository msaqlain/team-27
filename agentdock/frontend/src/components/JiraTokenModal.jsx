import React, { useEffect, useState } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle, TextField, Button, Alert } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import config from '../config';

// LocalStorage keys
const JIRA_TOKEN_KEY = 'jira_token';
const JIRA_MCP_URL_KEY = 'jira_mcp_url';
const JIRA_CONFIG_STATUS_KEY = 'jira_config_status';

/**
 * A reusable modal component for Jira token configuration
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the modal is open
 * @param {Function} props.onClose - Function to call when the modal is closed
 * @returns {JSX.Element} The JiraTokenModal component
 */
const JiraTokenModal = ({ open, onClose }) => {
  const [jiraToken, setJiraToken] = useState('');
  const [jiraEmail, setJiraEmail] = useState('');
  const [jiraUrl, setJiraUrl] = useState('');
  const [mcpServerUrl, setMcpServerUrl] = useState('http://localhost:8004');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [configStatus, setConfigStatus] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    // Load saved values from localStorage when modal opens
    if (open) {
      const savedConfig = localStorage.getItem(JIRA_TOKEN_KEY) ? JSON.parse(localStorage.getItem(JIRA_TOKEN_KEY)) : {};
      const savedMcpUrl = localStorage.getItem(JIRA_MCP_URL_KEY) || 'http://localhost:8004';
      const savedStatus = localStorage.getItem(JIRA_CONFIG_STATUS_KEY) || '';
      
      setJiraToken(savedConfig.token || '');
      setJiraEmail(savedConfig.email || '');
      setJiraUrl(savedConfig.url || '');
      setMcpServerUrl(savedMcpUrl);
      setConfigStatus(savedStatus);
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!jiraToken.trim()) {
      enqueueSnackbar('Please enter a Jira API token', { variant: 'error' });
      return;
    }

    if (!jiraEmail.trim()) {
      enqueueSnackbar('Please enter your Jira email', { variant: 'error' });
      return;
    }

    if (!jiraUrl.trim()) {
      enqueueSnackbar('Please enter your Jira instance URL', { variant: 'error' });
      return;
    }

    if (!mcpServerUrl.trim()) {
      enqueueSnackbar('Please enter an MCP Server URL', { variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      // Save values to localStorage
      const jiraConfig = {
        token: jiraToken,
        email: jiraEmail,
        url: jiraUrl
      };
      localStorage.setItem(JIRA_TOKEN_KEY, JSON.stringify(jiraConfig));
      localStorage.setItem(JIRA_MCP_URL_KEY, mcpServerUrl);
      
      // Update the config with the new MCP URL
      config.updateJiraMcpUrl();
      
      // Call the MCP server API (if available)
      try {
        await axios.post(`${mcpServerUrl}/configure`, { 
          token: jiraToken,
          email: jiraEmail,
          url: jiraUrl
        });
        
        // Update status in localStorage
        const timestamp = new Date().toLocaleString();
        const status = `Configured successfully at ${timestamp}`;
        localStorage.setItem(JIRA_CONFIG_STATUS_KEY, status);
        setConfigStatus(status);
        
        enqueueSnackbar('Jira configuration saved successfully', { variant: 'success' });
      } catch (error) {
        // Even if the MCP server fails, we still saved to localStorage
        console.error('Error configuring Jira with MCP server:', error);
        
        // Update status with warning
        const timestamp = new Date().toLocaleString();
        const status = `Configuration saved locally at ${timestamp}, but MCP server error: ${error.message}`;
        localStorage.setItem(JIRA_CONFIG_STATUS_KEY, status);
        setConfigStatus(status);
        
        enqueueSnackbar('Jira configuration saved locally, but MCP server not reachable', { variant: 'warning' });
      }
      
      onClose();
    } catch (error) {
      console.error('Error saving Jira configuration:', error);
      
      // Update status with error
      const timestamp = new Date().toLocaleString();
      const status = `Configuration failed at ${timestamp}: ${error.message}`;
      localStorage.setItem(JIRA_CONFIG_STATUS_KEY, status);
      setConfigStatus(status);
      
      enqueueSnackbar('Failed to save Jira configuration', { variant: 'error' });
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
      <DialogTitle>Configure Jira Access</DialogTitle>
      <DialogContent>
        {configStatus && (
          <Alert 
            severity={configStatus.includes('failed') ? 'error' : configStatus.includes('warning') ? 'warning' : 'success'} 
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
          helperText="URL of the Jira MCP Server (if available)"
          sx={{ marginBottom: 2 }}
        />
        
        <TextField
          margin="dense"
          label="Jira Instance URL"
          type="text"
          fullWidth
          variant="outlined"
          value={jiraUrl}
          onChange={(e) => setJiraUrl(e.target.value)}
          disabled={isSubmitting}
          placeholder="https://your-domain.atlassian.net"
          helperText="Your Jira instance URL"
          sx={{ marginBottom: 2 }}
        />
        
        <TextField
          margin="dense"
          label="Jira Email"
          type="email"
          fullWidth
          variant="outlined"
          value={jiraEmail}
          onChange={(e) => setJiraEmail(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your Jira email"
          helperText="The email associated with your Jira account"
          sx={{ marginBottom: 2 }}
        />
        
        <TextField
          margin="dense"
          label="Jira API Token"
          type="password"
          fullWidth
          variant="outlined"
          value={jiraToken}
          onChange={(e) => setJiraToken(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your Jira API token"
          helperText="Generate this token from your Atlassian account settings"
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

export default JiraTokenModal; 