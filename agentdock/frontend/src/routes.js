import React from "react";
import { Route, Routes } from "react-router-dom";
import ChatWithAgent from "./Pages/ChatWithAgent";
import AgentConfiguration from "./Pages/AgentConfiguration";

export default function Router() {
  return (
    <>
      <Routes>
        <Route path="/" element={<ChatWithAgent />} />
        <Route path="/agent-configuration" element={<AgentConfiguration />} />
      </Routes>
    </>
  );
}
