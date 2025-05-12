import React, { useEffect, useState } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle, TextField, Button, Alert } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import config from '../config';

// LocalStorage keys
const SLACK_TOKEN_KEY = 'slack_token';
const SLACK_MCP_URL_KEY = 'slack_mcp_url';
const SLACK_CONFIG_STATUS_KEY = 'slack_config_status';

/**
 * A reusable modal component for Slack token configuration
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the modal is open
 * @param {Function} props.onClose - Function to call when the modal is closed
 * @returns {JSX.Element} The SlackTokenModal component
 */
const SlackTokenModal = ({ open, onClose }) => {
  const [slackToken, setSlackToken] = useState('');
  const [mcpServerUrl, setMcpServerUrl] = useState('http://localhost:8003');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [configStatus, setConfigStatus] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    // Load saved values from localStorage when modal opens
    if (open) {
      const savedToken = localStorage.getItem(SLACK_TOKEN_KEY) || '';
      const savedMcpUrl = localStorage.getItem(SLACK_MCP_URL_KEY) || 'http://localhost:8003';
      const savedStatus = localStorage.getItem(SLACK_CONFIG_STATUS_KEY) || '';
      
      setSlackToken(savedToken);
      setMcpServerUrl(savedMcpUrl);
      setConfigStatus(savedStatus);
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!slackToken.trim()) {
      enqueueSnackbar('Please enter a Slack token', { variant: 'error' });
      return;
    }

    if (!mcpServerUrl.trim()) {
      enqueueSnackbar('Please enter an MCP Server URL', { variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      // Save values to localStorage
      localStorage.setItem(SLACK_TOKEN_KEY, slackToken);
      localStorage.setItem(SLACK_MCP_URL_KEY, mcpServerUrl);
      
      // Update the config with the new MCP URL
      config.updateSlackMcpUrl();
      
      // Call the MCP server API
      await axios.post(`${mcpServerUrl}/configure`, { token: slackToken });
      
      // Update status in localStorage
      const timestamp = new Date().toLocaleString();
      const status = `Configured successfully at ${timestamp}`;
      localStorage.setItem(SLACK_CONFIG_STATUS_KEY, status);
      setConfigStatus(status);
      
      enqueueSnackbar('Slack token configured successfully', { variant: 'success' });
      onClose();
    } catch (error) {
      console.error('Error configuring Slack token:', error);
      
      // Update status with error
      const timestamp = new Date().toLocaleString();
      const status = `Configuration failed at ${timestamp}: ${error.message}`;
      localStorage.setItem(SLACK_CONFIG_STATUS_KEY, status);
      setConfigStatus(status);
      
      enqueueSnackbar('Failed to configure Slack token', { variant: 'error' });
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
      <DialogTitle>Configure Slack Access</DialogTitle>
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
          helperText="URL of the Slack MCP Server"
          sx={{ marginBottom: 2 }}
        />
        
        <TextField
          margin="dense"
          label="Slack Token"
          type="password"
          fullWidth
          variant="outlined"
          value={slackToken}
          onChange={(e) => setSlackToken(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your Slack token"
          helperText="This token will be used to access your Slack workspace"
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

export default SlackTokenModal; 