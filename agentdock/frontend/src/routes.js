import React from "react";
import { Route, Routes } from "react-router-dom";
import ChatWithAgent from "./Pages/ChatWithAgent";

export default function Router() {
  return (
    <>
      <Routes>
        <Route path="/" element={<ChatWithAgent />} />
      </Routes>
    </>
  );
}
