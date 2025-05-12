import React, { useState } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle, TextField, Button } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const handleSubmit = async () => {
    if (!slackToken.trim()) {
      enqueueSnackbar('Please enter a Slack token', { variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.post('http://localhost:8001/configure/slack', { token: slackToken });
      enqueueSnackbar('Slack token configured successfully', { variant: 'success' });
      setSlackToken('');
      onClose();
    } catch (error) {
      console.error('Error configuring Slack token:', error);
      enqueueSnackbar('Failed to configure Slack token', { variant: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setSlackToken('');
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Configure Slack Access</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Slack Token"
          type="password"
          fullWidth
          variant="outlined"
          value={slackToken}
          onChange={(e) => setSlackToken(e.target.value)}
          disabled={isSubmitting}
          placeholder="Enter your Slack API token"
          helperText="This token will be used to access Slack data and send messages"
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