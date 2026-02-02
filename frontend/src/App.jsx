import React, { useState, useEffect, useLayoutEffect } from "react";
import { useLanguageTheme } from "./contexts/LanguageThemeContext";
import { useAuth } from "./contexts/AuthContext";
import { Sidebar } from "./components/Sidebar";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import { ChatMessages } from "./components/ChatMessages";
import { InputArea } from "./components/InputArea";
import { AuthScreen } from "./components/AuthScreen";
import { MdOutlineArrowLeft, MdOutlineArrowRight } from "react-icons/md";

export const App = () => {
  const { language, theme } = useLanguageTheme();
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isShowSidebar, setIsShowSidebar] = useState(false);
  const [isInputCentered, setIsInputCentered] = useState(true);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  
  // Track window width for the 700px breakpoint logic
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const isSmallScreen = windowWidth < 900;

  // --- LOGIC ---
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchConversations();
    }
  }, [isAuthenticated, token]);

  const fetchConversations = async () => {
    setConversationsLoading(true);
    try {
      const response = await fetch("http://localhost:5000/conversations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setConversationsLoading(false);
    }
  };

  const fetchConversationMessages = async (conversationId) => {
    try {
      const response = await fetch(`http://localhost:5000/conversations/${conversationId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        return data.messages.map((msg) => ({ role: msg.role, content: msg.content }));
      }
      return [];
    } catch (error) {
      console.error("Error fetching messages:", error);
      return [];
    }
  };

  useLayoutEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
      setIsShowSidebar(window.innerWidth > 768);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleNewChat = () => {
    setMessages([]);
    setIsInputCentered(true);
    setCurrentConversationId(null);
    if (window.innerWidth <= 768) setIsShowSidebar(false);
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;
    setIsInputCentered(false);
    setIsLoading(true);

    const userMessage = text;
    const updatedMessages = [
      ...messages,
      { role: "user", content: userMessage },
      { role: "assistant", content: "" },
    ];
    setMessages(updatedMessages);

    try {
      const testModelVersionId = "default-model-v1";
      const response = await fetch("http://localhost:5000/chat_stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: currentConversationId,
          model_version_id: testModelVersionId,
        }),
      });

      if (!response.ok || !response.body) throw new Error("Server error");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let displayedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk
          .split("\n")
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.replace(/^data:\s*/, "").trim());

        for (const line of lines) {
          if (line === "[DONE]") break;
          displayedText += line + " ";
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1].content = displayedText.trim();
            return updated;
          });
        }
      }
      await fetchConversations();
      if (!currentConversationId) {
        const convResponse = await fetch("http://localhost:5000/conversations", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (convResponse.ok) {
          const data = await convResponse.json();
          if (data.conversations?.length > 0) setCurrentConversationId(parseInt(data.conversations[0].id));
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = async (id) => {
    const conversationId = parseInt(id);
    setCurrentConversationId(conversationId);
    setIsInputCentered(false);
    const conversationMessages = await fetchConversationMessages(conversationId);
    setMessages(conversationMessages);
    if (window.innerWidth <= 768) setIsShowSidebar(false);
  };

  const handleDeleteConversation = async (id) => {
    try {
      const response = await fetch(`http://localhost:5000/conversations/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        if (currentConversationId === parseInt(id)) handleNewChat();
        await fetchConversations();
      }
    } catch (error) {
      console.error("Error deleting:", error);
    }
  };

  const bgColor = isDark ? "#232323" : "#f1f1f1";

  if (authLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100dvh', backgroundColor: bgColor }}>
        <div style={{ color: isDark ? '#ffffff' : '#000000', fontSize: '18px' }}>
          {isArabic ? 'جاري التحميل...' : 'Loading...'}
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return <AuthScreen />;

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        backgroundColor: bgColor,
        direction: isArabic ? "rtl" : "ltr",
        overflow: "hidden",
        margin: 0,
        padding: 0,
        position: "fixed",
        top: 0,
        left: 0,
      }}
    >
      <Sidebar
        isOpen={isShowSidebar}
        onToggle={() => setIsShowSidebar((prev) => !prev)}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        conversations={conversations}
        conversationsLoading={conversationsLoading}
        currentConversationId={currentConversationId}
      />

      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          position: "relative",
          height: "100%",
          minWidth: 0,
          transition: "all 0.3s ease-in-out",
        }}
      >
        {/* Toggle Button Container */}
        <div style={{ 
          position: "absolute", 
          top: "16px", 
          [isArabic ? "right" : "left"]: "16px", 
          zIndex: 30 
        }}>
          <button
            onClick={() => setIsShowSidebar(!isShowSidebar)}
            style={{
              padding: "8px",
              backgroundColor: isDark ? "rgba(74, 75, 74, 0.8)" : "rgba(229, 229, 229, 0.8)",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              boxShadow: "0 2px 5px rgba(0,0,0,0.1)"
            }}
          >
            {isShowSidebar ? (
              isArabic ? <MdOutlineArrowRight size={24} color={isDark ? "#ffffff" : "#000000"} /> 
                       : <MdOutlineArrowLeft size={24} color={isDark ? "#ffffff" : "#000000"} />
            ) : (
              isArabic ? <MdOutlineArrowLeft size={24} color={isDark ? "#ffffff" : "#000000"} /> 
                       : <MdOutlineArrowRight size={24} color={isDark ? "#ffffff" : "#000000"} />
            )}
          </button>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column", position: "relative" }}>
          {messages.length === 0 ? (
            <WelcomeScreen />
          ) : (
            <ChatMessages messages={messages} isLoading={isLoading} />
          )}
        </div>

        {/* Input Container - GEMINI STYLE */}
        <div style={{
          width: "100%",
          display: "flex",
          justifyContent: "center",
          padding: isSmallScreen ? "0 10px 15px 10px" : "0 20px 30px 20px",
          boxSizing: "border-box",
          zIndex: 10,
          // If centered, the InputArea component handles its own absolute positioning.
          // If not centered, it stays naturally at the bottom of this flex column.
        }}>
          <div style={{ width: "100%", maxWidth: "850px" }}>
            <InputArea
              onSend={handleSendMessage}
              isLoading={isLoading}
              // FIX: Force centered to FALSE if window is small, otherwise use logic
              isCentered={!isSmallScreen && isInputCentered && messages.length === 0}
            />
          </div>
        </div>
      </main>
      
      {/* Mobile Overlay */}
      {windowWidth <= 768 && isShowSidebar && (
        <div 
          onClick={() => setIsShowSidebar(false)}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.4)",
            zIndex: 35
          }}
        />
      )}
    </div>
  );
};

export default App;