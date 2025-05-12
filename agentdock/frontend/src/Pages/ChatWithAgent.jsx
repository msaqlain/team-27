import React, { useState, useRef, useEffect } from "react";
import { useSnackbar } from "notistack";
import { 
  ArrowUpIcon, 
  PlusIcon, 
  SparklesIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  SettingsIcon,
  TrashIcon} from "../components/icons.tsx";
import { DoChat } from "../DAL/Chat/chat.js";
import { CHAT_WITH_AGENT_SCREEN_HEIGHT } from "../constants/AppConstants.js";
import SettingsPanel from "../components/SettingsPanel";

import './ChatWithAgent.css'

export default function ChatWithAgent() {
  const containerRef = useRef(null);
  const { enqueueSnackbar } = useSnackbar();
  const [mainDashboard, setMainDashboard] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const [activeThreadId, setActiveThreadId] = useState(null);
  
  // Settings state
  const [showSettings, setShowSettings] = useState(false);

  const [input, setInput] = useState("");
  const [openLoader, setOpenLoader] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [chatScreenHeight, setChatScreenHeight] = useState(mainDashboard ? "30vh" : CHAT_WITH_AGENT_SCREEN_HEIGHT);

  // Initialize state with empty arrays/objects
  const [conversations, setConversations] = useState([]);
  const [threadsMessages, setThreadsMessages] = useState({});
  const [messages, setMessages] = useState([]);

  // Initialize speech recognition
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

  // Load conversations and threads from localStorage on component mount
  useEffect(() => {
    const storedConversations = localStorage.getItem('conversations');
    const storedThreadsMessages = localStorage.getItem('threadsMessages');
    const storedActiveThreadId = localStorage.getItem('activeThreadId');
    
    if (storedConversations) {
      setConversations(JSON.parse(storedConversations));
      setMainDashboard(false);
    }
    
    if (storedThreadsMessages) {
      setThreadsMessages(JSON.parse(storedThreadsMessages));
    }
    
    if (storedActiveThreadId) {
      setActiveThreadId(JSON.parse(storedActiveThreadId));
      
      // If there was an active thread, load its messages
      if (storedThreadsMessages) {
        const threadsData = JSON.parse(storedThreadsMessages);
        if (threadsData[storedActiveThreadId]) {
          setMessages(threadsData[storedActiveThreadId]);
          setMainDashboard(false);
          setChatScreenHeight(CHAT_WITH_AGENT_SCREEN_HEIGHT);
        }
      }
    }

    // Also check for standalone messages (for backward compatibility)
    const storedMessages = sessionStorage.getItem("messages");
    if (storedMessages && !storedActiveThreadId) {
      setMessages(JSON.parse(storedMessages));
    }
    
    setTimeout(() => {
      setScroll();
    }, 200);
  }, []);

  // Save conversations and threads to localStorage when they change
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }else {
      localStorage.removeItem('conversations');
      localStorage.removeItem('threadsMessages');
      localStorage.removeItem('activeThreadId');
      setMainDashboard(true);
      setChatScreenHeight("30vh");
    }
  }, [conversations]);

  useEffect(() => {
    if (Object.keys(threadsMessages).length > 0) {
      localStorage.setItem('threadsMessages', JSON.stringify(threadsMessages));
    }
  }, [threadsMessages]);

  useEffect(() => {
    if (activeThreadId) {
      localStorage.setItem('activeThreadId', JSON.stringify(activeThreadId));
    }
  }, [activeThreadId]);

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

  const createNewThread = () => {
    const newThreadId = Date.now();
    
    const newThread = {
      id: newThreadId,
      title: "New Conversation",
    };
    
    setConversations(prev => [newThread, ...prev]);
    
    setMessages([]);
    
    setActiveThreadId(newThreadId);
    
    setMainDashboard(false);
    setSidebarCollapsed(false);
    
    setChatScreenHeight(CHAT_WITH_AGENT_SCREEN_HEIGHT);
    
    enqueueSnackbar("New conversation started", { variant: "success" });
  };


  const deleteThread = (threadId, event) => {
    // Stop event propagation to prevent selecting the thread
    event.stopPropagation();
    
    // Remove the thread from conversations
    setConversations(prev => prev.filter(conv => conv.id !== threadId));
    
    // Remove the thread messages
    setThreadsMessages(prev => {
      const updated = {...prev};
      delete updated[threadId];
      return updated;
    });
    
    // If the active thread is deleted, reset to main dashboard or select first available thread
    if (activeThreadId === threadId) {
      if (conversations.length <= 1) {
        // If this was the last thread, go back to main dashboard
        setActiveThreadId(null);
        setMessages([]);
        setMainDashboard(true);
      } else {
        // Select another thread
        const remainingThreads = conversations.filter(conv => conv.id !== threadId);
        if (remainingThreads.length > 0) {
          const nextThreadId = remainingThreads[0].id;
          setActiveThreadId(nextThreadId);
          setMessages(threadsMessages[nextThreadId] || []);
        }
      }
    }
    
    enqueueSnackbar("Conversation deleted", { variant: "success" });
  };
  
  const selectThread = (threadId) => {
    setActiveThreadId(threadId);
    
    if (threadsMessages[threadId]) {
      setMessages(threadsMessages[threadId]);
    } else {
      setMessages([]);
    }
    
    setMainDashboard(false);
    setSidebarCollapsed(true);
    
    setChatScreenHeight(CHAT_WITH_AGENT_SCREEN_HEIGHT);
    
    setTimeout(() => {
      setScroll();
    }, 100);
  };

  const cleanAssistantMessage = (html) => {
    return html.replace(/(\d+\.)\s+(\S)/g, '$1 $2');
  };
  
  const setScroll = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    
    let newThreadId = activeThreadId;
    
    if (!newThreadId) {
      newThreadId = Date.now();
      setActiveThreadId(newThreadId);
      setConversations(prev => [{
        id: newThreadId,
        title: input.slice(0, 20) + (input.length > 20 ? "..." : "")
      }, ...prev]);
    }
    
    setMainDashboard(false);
    setSidebarCollapsed(true);
    setChatScreenHeight(CHAT_WITH_AGENT_SCREEN_HEIGHT);
    
    const currentMessages = [...messages];
    
    const userMessage = { 
      user: input,
      assistant: "Processing your question..."
    };
    
    const updatedMessages = [...currentMessages, userMessage];
    setMessages(updatedMessages);
    
    setThreadsMessages(prev => ({
      ...prev,
      [newThreadId]: updatedMessages
    }));
    
    if (currentMessages.length === 0) {
      setConversations(prev => 
        prev.map(conv => 
          conv.id === newThreadId 
            ? { ...conv, title: input.slice(0, 20) + (input.length > 20 ? "..." : "") } 
            : conv
        )
      );
    }

    setInput("");
    setOpenLoader(true);
    setIsWaitingForResponse(true);

    setTimeout(() => {
      setScroll();
    }, 500);

    try {
      const lastThreeMessages = currentMessages.slice(-3);
      const stream = DoChat(input, lastThreeMessages);
      let aiReply = "";

      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            assistant: "Processing your question..."
          };
        }
        return updated;
      });

      let previousChunk = "";

      for await (const chunk of stream) {
        const newText = chunk.slice(previousChunk.length);
        previousChunk = chunk;

        const formattedChunk = newText.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

        setMessages(prev => {
          const updated = [...prev];
          if (updated.length > 0) {
            const currentAssistantMessage = updated[updated.length - 1].assistant || "";
            
            // Replace "Processing your question..." with the first chunk, then append to the response for subsequent chunks
            if (currentAssistantMessage === "Processing your question...") {
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                assistant: formattedChunk
                  .replace(/(?<!\d)\. /g, '.\n')
                  .replace("? ", "?\n"),
              };
            } else {
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                assistant: (currentAssistantMessage + formattedChunk)
                  .replace(/(?<!\d)\. /g, '.\n')
                  .replace("? ", "?\n"),
              };
            }
          }
          
          if (activeThreadId) {
            setThreadsMessages(prevThreads => ({
              ...prevThreads,
              [activeThreadId]: updated
            }));
          }
          
          return updated;
        });

        setTimeout(() => {
          setScroll();
        }, 200);
      }
      
      setOpenLoader(false);
      setIsWaitingForResponse(false);

    } catch (error) {
      enqueueSnackbar(`Error while streaming response ${error}`);
      setOpenLoader(false);
      setIsWaitingForResponse(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Toggle settings view
  const handleToggleSettings = () => {
    setShowSettings(prev => !prev);
    // if (sidebarCollapsed) {
    //   setSidebarCollapsed(false);
    // }
  };

  // Go back to chat
  const handleBackToChat = () => {
    setShowSettings(false);
  };

  return (
    <div className="flex flex-col h-screen bg-white-100 chat-container">
      {mainDashboard && sidebarCollapsed && <div className="fixed top-4 left-4 z-10 flex gap-2">
        <button
          className="p-2 bg-white rounded-full shadow-md hover:shadow-lg flex items-center justify-center"
          onClick={handleToggleSettings}
          aria-label="settings"
          title="Integration Settings"
          id="settings-button"
        >
          <SettingsIcon size={20} currentColor="#1976d2" />
        </button>
      </div>}
      
      <div className="flex h-full" style={{ paddingLeft: "20px", paddingRight: "20px" }}>
        <div className={sidebarCollapsed ? '': 'w-1/5 pl-4'}>
          <div
            className={`fixed top-0 left-0 h-full bg-gray-100 shadow-lg transform transition-transform duration-500 ${
              !sidebarCollapsed ? "translate-x-0" : "-translate-x-full"
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
                  onClick={createNewThread}
                  title="New conversation"
                >
                  <PlusIcon size={20} currentColor={"#6b7280"} className="mr-2 gray-500" />
                </button>
              </div>
            </div>

            <div className="flex flex-col h-[calc(100%-80px)] justify-between">
              <div className="mt-4 pl-3 pr-3 block flex-grow overflow-auto">
                <div className="mb-4">
                  <ul className="mt-2">
                    {conversations.map((chat) => (
                      <li 
                        key={chat.id} 
                        className={`p-2 rounded-md hover:bg-gray-200 cursor-pointer ${activeThreadId === chat.id && !showSettings ? 'bg-gray-200' : ''}`}
                      >
                         <div className="flex justify-between items-center">
                          <button 
                            onClick={() => {
                              selectThread(chat.id);
                              setShowSettings(false);
                            }} 
                            value={chat.id}
                            className="w-full text-left overflow-hidden overflow-ellipsis whitespace-nowrap"
                          > 
                            {chat.title} 
                          </button>
                          <button
                            onClick={(e) => deleteThread(chat.id, e)}
                            className="p-1 hover:bg-gray-300 rounded-full"
                            title="Delete conversation"
                            aria-label="Delete conversation"
                          >
                            <TrashIcon size={16} currentColor="#6b7280" />
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              
              {/* Settings button at bottom of sidebar */}
              <div className="pl-3 pr-3 pb-4">
                <button
                  className={`w-full p-2 flex items-center justify-between rounded-md hover:bg-gray-200 ${showSettings ? 'bg-gray-200' : ''}`}
                  onClick={handleToggleSettings}
                >
                  <div className="flex items-center">
                    <SettingsIcon size={20} currentColor="#6b7280" />
                    <span className="ml-2 text-gray-700">Settings</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
          
          {/* Collapse/Expand button */}
          {conversations.length > 0 && (
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
          {!showSettings ? (
            // Chat UI
            <>
              {!mainDashboard ? <div
                ref={containerRef}
                style={{ height: chatScreenHeight }}
                className="flex-1 overflow-auto pl-4 pr-4 pt-4 mt-5 space-y-2 transition-all duration-700"
              >
                {messages.map((msg, index) => (
                  <div key={index}>
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

                    {msg.assistant && (
                      <div className="flex justify-start mt-2">
                        <div className="flex items-start space-x-2">
                          <div className="rounded-full self-start p-2 border">
                            <SparklesIcon size={15} />
                          </div>
                          <div
                            className="p-4 rounded-lg shadow-md max-w-full whitespace-pre-line bg-white text-gray-900 border"
                          >
                            {msg.assistant === "Processing your question..." ? (
                              <div className="flex items-center">
                                <span>Processing your question</span>
                                <span className="ml-1 dots-animation">...</span>
                              </div>
                            ) : (
                              <p dangerouslySetInnerHTML={{ __html: cleanAssistantMessage(msg.assistant) }} />
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div> : <div
                ref={containerRef}
                style={{ height: chatScreenHeight }}
                className="flex-1 overflow-auto pl-4 pr-4 pt-4 mt-5 space-y-2 transition-all duration-700"
              ></div>}
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
                      className={`w-full p-3 bg-gray-100 text-gray-800 outline-none resize-none ${isWaitingForResponse ? 'opacity-60 cursor-not-allowed' : ''}`}
                      placeholder={isWaitingForResponse ? "Waiting for response..." : "Send a message..."}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      disabled={openLoader || isWaitingForResponse}
                      onKeyDown={handleKeyDown}
                    />
                    <div className="flex mt-2 self-end">
                      <button
                        className="mr-2 p-2 bg-blue-600 text-white hover:bg-blue-700 rounded-full"
                        onClick={handleMicClick}
                        disabled={openLoader || isWaitingForResponse}
                      >
                        {isListening ? "Stop 🎙️" : "Talk 🎤"}
                      </button>
                      <button
                        className={`p-2 Sendbtn-bg text-white hover:bg-gray-500 rounded-full ${(openLoader || isWaitingForResponse) ? 'opacity-60 cursor-not-allowed' : ''}`}
                        onClick={handleSend}
                        disabled={openLoader || isWaitingForResponse}
                        style={{
                          width: "40px",
                          height: "40px",
                          alignItems: "center",
                          justifyContent: "center",
                          textAlign: "center",
                          display: "flex",
                        }}
                      >
                        <ArrowUpIcon size={15} />
                      </button>
                    </div>
                  </div>
                </center>
              </div>
            </>
          ) : (
            // Settings Panel
            <SettingsPanel
              onBackToChat={handleBackToChat}
            />
          )}
        </div>
      </div>
    </div>
  );
}