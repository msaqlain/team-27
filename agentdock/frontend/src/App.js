import React from "react";
import "./App.css";
import { SnackbarProvider } from "notistack";
import { IconButton, Slide } from "@mui/material";
import Router from "./routes";
import ChatWithAgent from "./Pages/ChatWithAgent";
import AgentConfiguration from "./Pages/AgentConfiguration";
import { Route, Routes } from "react-router-dom";

// import CloseIcon from "@mui/icons-material/Close";

function App() {
  const notiStackRef = React.createRef();
  const onClickDismiss = (key) => () => {
    notiStackRef.current.closeSnackbar(key);
  };
  return (
    <>
      <SnackbarProvider
        hideIconVariant
        ref={notiStackRef}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        TransitionComponent={Slide}
        maxSnack={3}
        autoHideDuration={3000}
        action={(key) => (
          <IconButton onClick={onClickDismiss(key)}>
            {/* <CloseIcon htmlColor="white" /> */}
          </IconButton>
        )}
      >
        <div style={{ display: 'flex' }}>
          <div style={{ marginLeft: '0px', width: '100%', marginRight: '0px', marginTop: '0px' }}>
          <Router />
          </div>
        </div>
      </SnackbarProvider>
    </>
  );
}

export default App;
