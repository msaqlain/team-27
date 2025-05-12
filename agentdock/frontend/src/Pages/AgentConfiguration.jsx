import { useState } from "react";
import { Button, TextField, Typography, Snackbar, Alert, Box } from "@mui/material";
import axios from "axios";

const AgentConfiguration = () => {
  const [token, setToken] = useState("");
  const [open, setOpen] = useState(false);
  const [success, setSuccess] = useState(true);

  const handleSubmit = async () => {
    try {
      await axios.post("http://localhost:8001/configure", { token });
      setSuccess(true);
      setOpen(true);
    } catch (error) {
      setSuccess(false);
      setOpen(true);
    }
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Box sx={{ padding: 3 }}>
      <Typography variant="h5" gutterBottom>
        Configure GitHub Access
      </Typography>
      <TextField
        label="GitHub Token"
        type="password"
        variant="outlined"
        fullWidth
        value={token}
        onChange={(e) => setToken(e.target.value)}
        sx={{ maxWidth: 400, marginBottom: 2 }}
      />
      <br />
      <Button variant="contained" color="primary" onClick={handleSubmit}>
        Submit
      </Button>

      <Snackbar open={open} autoHideDuration={3000} onClose={handleClose}>
        <Alert severity={success ? "success" : "error"} onClose={handleClose} sx={{ width: "100%" }}>
          {success ? "GitHub token configured successfully" : "Failed to configure GitHub token"}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentConfiguration;
