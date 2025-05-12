import React, { useState } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle, TextField, Button } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

/**
 * A reusable modal component for Jira token configuration
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the modal is open
 * @param {Function} props.onClose - Function to call when the modal is closed
 * @returns {JSX.Element} The JiraTokenModal component
 */
const JiraTokenModal = ({ open, onClose }) => {
  const [jiraApiToken, setJiraApiToken] = useState('');
  const [jiraEmail, setJiraEmail] = useState('');
  const [jiraDomain, setJiraDomain] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const handleSubmit = async () => {
    if (!jiraApiToken.trim() || !jiraEmail.trim() || !jiraDomain.trim()) {
      enqueueSnackbar('Please fill in all Jira fields', { variant: 'error' });
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(jiraEmail)) {
      enqueueSnackbar('Please enter a valid email address', { variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.post('http://localhost:8001/configure/jira', { 
        token: jiraApiToken,
        email: jiraEmail,
        domain: jiraDomain
      });
      enqueueSnackbar('Jira configuration successful', { variant: 'success' });
      resetForm();
      onClose();
    } catch (error) {
      console.error('Error configuring Jira:', error);
      enqueueSnackbar('Failed to configure Jira', { variant: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setJiraApiToken('');
    setJiraEmail('');
    setJiraDomain('');
  };

  const handleClose = () => {
    if (!isSubmitting) {
      resetForm();
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Configure Jira Access</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Jira Email"
          type="email"
          fullWidth
          variant="outlined"
          value={jiraEmail}
          onChange={(e) => setJiraEmail(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your Jira email address"
        />
        <TextField
          margin="dense"
          label="Jira API Token"
          type="password"
          fullWidth
          variant="outlined"
          value={jiraApiToken}
          onChange={(e) => setJiraApiToken(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your Jira API token"
        />
        <TextField
          margin="dense"
          label="Jira Domain"
          type="text"
          fullWidth
          variant="outlined"
          value={jiraDomain}
          onChange={(e) => setJiraDomain(e.target.value)}
          disabled={isSubmitting}
          placeholder="e.g., your-company.atlassian.net"
          helperText="This information will be used to access your Jira projects and issues"
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