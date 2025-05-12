import React, { useState, useRef, useEffect } from "react";
import { useSnackbar } from "notistack";
import { ArrowUpIcon, PlusIcon, SparklesIcon, ChevronLeftIcon, ChevronRightIcon } from "../components/icons.tsx";
import { useNavigate } from "react-router-dom";
import { Button } from "@mui/material";
import { DoChat } from "../DAL/Chat/chat.js";

import './ChatWithAgent.css'

export default function ChatWithAgent() {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const { enqueueSnackbar } = useSnackbar();
  const [mainDashboard, setMainDashboard] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const [input, setInput] = useState("");
  const [openLoader, setOpenLoader] = useState(false);
  const [chatScreenHeight, setChatScreenHeight] = useState("30vh");

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.continuous = false;
  
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
        // Optional: send automatically
        // handleSend();
      };
  
      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };
  
      recognition.onend = () => {
        setIsListening(false);
      };
  
      recognitionRef.current = recognition;
    }
  }, []);

  const handleMicClick = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setInput(""); // clear previous input
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const conversations = {
    // TODO: Should be fetched from API 
    "Today": [],
    "Yesterday": [
      { id: 3, title: "Sample Conversation" },
    ]
  };

  const [history, setHistory] = useState(conversations);

  const cleanAssistantMessage = (html) => {
    return html.replace(/(\d+\.)\s+(\S)/g, '$1 $2');
  };
  
  // Scroll to the bottom of the chat container
  const setScroll = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };
  
  // Initialize messages to an empty array
  const [messages, setMessages] = useState([]);

  // Handle sending a message
  const handleSend = async () => {
    if (!input.trim()) return; // Prevent sending empty messages
    setMainDashboard(false);
    setSidebarCollapsed(true); // Ensure sidebar is collapsed by default when starting chat
    setChatScreenHeight("78vh");
    
    // Create a deepcopy of the current messages
    const currentMessages = [...messages];
    
    // Display user's new message on UI
    const userMessage = { 
      user: input,
      assistant: "Thinking..."
    };
    setMessages([...currentMessages, userMessage]); // Update state

    setInput(""); // Clear input
    setOpenLoader(true);

    setTimeout(() => {
      setScroll();
    }, 500);

    try {
      const lastThreeMessages = currentMessages.slice(-3);
      const stream = DoChat(input, lastThreeMessages);
      let aiReply = "";

      setMessages(prev => {
        const updated = [...prev];
        // Replace the "Thinking..." with "Searching..."
        if (updated.length > 0) {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            assistant: "Searching..."
          };
        }
        return updated;
      });

      let previousChunk = "";

      for await (const chunk of stream) {
        const newText = chunk.slice(previousChunk.length); // only get the new part
        previousChunk = chunk;

        const formattedChunk = newText.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

        setMessages(prev => {
          const updated = [...prev];
          if (updated.length > 0) {
            const currentAssistantMessage = updated[updated.length - 1].assistant || "";
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              assistant: (currentAssistantMessage + formattedChunk)
                .replace(/(?<!\d)\. /g, '.\n')
                .replace("? ", "?\n"),
            };
          }
          return updated;
        });

        setTimeout(() => {
          setScroll();
        }, 200);
      }
      

      setOpenLoader(false);

    } catch (error) {
      enqueueSnackbar(`Error while streaming response ${error}`);
      setOpenLoader(false);
    }
  };

  // Handle Enter key press
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevent new line
      handleSend();
    }
  };

  // Load messages from session storage on component mount
  useEffect(() => {
    const storedMessages = sessionStorage.getItem("messages");
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages));
    }
    setScroll();
  }, []);

  return (
    <div className="flex flex-col h-screen bg-white-100 chat-container">
      <div className="flex h-full" style={{ paddingLeft: "20px", paddingRight: "20px" }}>
        <div className={mainDashboard || sidebarCollapsed ? '': 'w-1/5 pl-4'}>
          <div
            className={`fixed top-0 left-0 h-full bg-gray-100 shadow-lg transform transition-transform duration-500 ${
              !mainDashboard && !sidebarCollapsed ? "translate-x-0" : "-translate-x-full"
            }`}
            style={{ width: "20%" }}
          >
            <div className="p-4 bg-gray-100 text-white text-md font-bold flex justify-between">
              <div className="bg-gray-100 text-white text-md font-bold flex justify-between">
                <div style={{ display: "inline-block" }} className="text-gray-500">
                  <img src={`${process.env.PUBLIC_URL}/logo.png`} width='60px' height='25px' alt="Logo" style={{display: 'inline-block'}} />
                </div>
              </div>
              <div style={{ display: "inline-block", marginTop: "10px" }}>
                <button
                  onClick={() => {
                    enqueueSnackbar("Feature not implemented yet. New chat functionality is in progress.");
                  }}
                >
                  <PlusIcon size={20} currentColor={"#6b7280"} className="mr-2 gray-500" />
                </button>
              </div>
            </div>

            <div className={`mt-4 pl-3 block`}>
            <div className={`mt-4 pl-3 block`}>
              {Object.keys(conversations).map((date) => (
                <div key={date} className="mb-4">
                  <h3 className="text-gray-500 text-sm uppercase">{date}</h3>
                  <ul className="mt-2">
                    {conversations[date].map((chat) => (
                      <li key={chat.id} className="p-2 rounded-md hover:bg-gray-200 cursor-pointer">
                        <button onClick={() => enqueueSnackbar("Feature not implemented yet. New chat functionality is in progress.")} value={chat.id}> {chat.title} </button> 
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

           <Button
            variant="contained"
            color="primary"
            onClick={() => navigate("/agent-configuration")}
          >
            Configure GitHub Access
          </Button>
            </div>
          </div>
          
          {/* Collapse/Expand button */}
          {!mainDashboard && (
            <div 
              className={`fixed top-1/2 ${sidebarCollapsed ? 'left-0' : 'left-[20%]'} z-10 bg-gray-200 p-2 rounded-r-md cursor-pointer shadow-md transition-all duration-500 sidebar-toggle`}
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {sidebarCollapsed ? 
                <ChevronRightIcon size={24} currentColor={"#6b7280"} /> : 
                <ChevronLeftIcon size={24} currentColor={"#6b7280"} />
              }
            </div>
          )}
        </div>
        <div className={`${mainDashboard || sidebarCollapsed ? 'w-full' : 'w-4/5'} transition-all duration-500`}>
          <div
            ref={containerRef}
            style={{ height: chatScreenHeight }}
            className="flex-1 overflow-auto pl-4 pr-4 pt-4 mt-5 space-y-2 transition-all duration-700"
          >
            {messages.map((msg, index) => (
              <div key={index}>
                {/* User message aligned to the right */}
                {msg.user && (
                  <div className="flex justify-end">
                    <div className="flex items-start space-x-2">
                      <div
                        className="p-4 rounded-lg shadow-md max-w-full whitespace-pre-line bg-gray-200 text-gray-900"
                      >
                        <p>{msg.user}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Assistant message aligned to the left */}
                {msg.assistant && (
                  <div className="flex justify-start mt-2">
                    <div className="flex items-start space-x-2">
                      <div className="rounded-full self-start p-2 border">
                        <SparklesIcon size={15} />
                      </div>
                      <div
                        className="p-4 rounded-lg shadow-md max-w-full whitespace-pre-line bg-white text-gray-900 border"
                      >
                        <p dangerouslySetInnerHTML={{ __html: cleanAssistantMessage(msg.assistant) }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div>
            <center>
              {
                mainDashboard
                &&
                <div className="logoContainer" style={{ paddingBottom: '20px' }}>
                  <img src={`${process.env.PUBLIC_URL}/logo.png`} width='150px' height='70px' alt="Logo" />
                </div>
              }
              <div
                style={{
                  width: mainDashboard ? "50%" : "60%",
                  backgroundColor: "#f4f4f5",
                  marginBottom: "20px",
                  padding: "5px",
                  border: mainDashboard ? 'none' : "1px solid black",
                }}
                className="p-1 border flex flex-col items-start shadow-md mx-3 my-2 rounded-xl transition-all duration-100 focus-within:border-2 focus-within:border-black"
              >
                <textarea
                  className="w-full p-3 bg-gray-100 text-gray-800 rounded-full outline-none resize-none"
                  placeholder="Send a message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={openLoader}
                  onKeyDown={handleKeyDown}
                />
                <button
                  className="mt-2 p-2 Sendbtn-bg text-white hover:bg-gray-500 rounded-full self-end"
                  onClick={handleSend}
                  disabled={openLoader}
                >
                  <ArrowUpIcon size={15} />
                </button>
                <button
                  className="mt-2 ml-2 p-2 bg-blue-600 text-white hover:bg-blue-700 rounded-full self-end"
                  onClick={handleMicClick}
                  disabled={openLoader}
                >
                  {isListening ? "Stop 🎙️" : "Talk 🎤"}
                </button>
              </div>
            </center>
          </div>
        </div>
      </div>
    </div>
  );
}