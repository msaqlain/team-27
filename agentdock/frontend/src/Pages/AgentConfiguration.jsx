import { useState } from "react";
import {
  Button,
  TextField,
  Typography,
  Snackbar,
  Alert,
  Box,
  Divider,
} from "@mui/material";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const AgentConfiguration = () => {
  const navigate = useNavigate()
  const [githubToken, setGithubToken] = useState("");
  const [slackToken, setSlackToken] = useState("");
  const [open, setOpen] = useState(false);
  const [success, setSuccess] = useState(true);
  const [message, setMessage] = useState("");

  const handleGithubSubmit = async () => {
    try {
      await axios.post("http://localhost:8001/configure", { token: githubToken });
      setSuccess(true);
      setMessage("GitHub token configured successfully");
    } catch (error) {
      setSuccess(false);
      setMessage("Failed to configure GitHub token");
    } finally {
      setOpen(true);
    }
  };

  const handleSlackSubmit = async () => {
    try {
      await axios.post("http://localhost:8003/configure", { token: slackToken });
      setSuccess(true);
      setMessage("Slack token configured successfully");
    } catch (error) {
      setSuccess(false);
      setMessage("Failed to configure Slack token");
    } finally {
      setOpen(true);
    }
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Box sx={{ padding: 3 }}>
      <Button
        variant="contained"
        color="primary"
        sx={{ position: "absolute", top: 16, right: 16 }}
        onClick={() => navigate("/")}
      >
        Chatbot
      </Button>
      {/* GitHub Token Configuration */}
      <Typography variant="h5" gutterBottom>
        Configure GitHub Access
      </Typography>
      <TextField
        label="GitHub Token"
        type="password"
        variant="outlined"
        fullWidth
        value={githubToken}
        onChange={(e) => setGithubToken(e.target.value)}
        sx={{ maxWidth: 400, marginBottom: 2 }}
      />
      <br />
      <Button variant="contained" color="primary" onClick={handleGithubSubmit}>
        Submit GitHub Token
      </Button>

      <Divider sx={{ my: 4 }} />

      {/* Slack Token Configuration */}
      <Typography variant="h5" gutterBottom>
        Configure Slack Access
      </Typography>
      <TextField
        label="Slack Token"
        type="password"
        variant="outlined"
        fullWidth
        value={slackToken}
        onChange={(e) => setSlackToken(e.target.value)}
        sx={{ maxWidth: 400, marginBottom: 2 }}
      />
      <br />
      <Button variant="contained" color="primary" onClick={handleSlackSubmit}>
        Submit Slack Token
      </Button>

      {/* Shared Snackbar for Feedback */}
      <Snackbar open={open} autoHideDuration={3000} onClose={handleClose}>
        <Alert severity={success ? "success" : "error"} onClose={handleClose} sx={{ width: "100%" }}>
          {message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentConfiguration;
