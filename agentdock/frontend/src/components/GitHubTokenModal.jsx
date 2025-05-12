import React, { useEffect, useState } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle, TextField, Button } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    handleSlackSubmit()
  },[])

  const handleSlackSubmit = async () => {
    try {
      const slackToken = "xoxb-8903182592848-8884517421220-Y13IGtV5qRSaxi9SjbogytFv"
      await axios.post("http://localhost:8003/configure", { token: slackToken });
    }
    catch (err) {
      console.log(err)
    }
  };
  const handleSubmit = async () => {
    if (!githubToken.trim()) {
      enqueueSnackbar('Please enter a GitHub token', { variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.post('http://localhost:8001/configure', { token: githubToken });
      enqueueSnackbar('GitHub token configured successfully', { variant: 'success' });
      setGithubToken('');
      onClose();
    } catch (error) {
      console.error('Error configuring GitHub token:', error);
      enqueueSnackbar('Failed to configure GitHub token', { variant: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setGithubToken('');
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Configure GitHub Access</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
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