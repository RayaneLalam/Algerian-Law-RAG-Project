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

  // Load conversations from localStorage
  useEffect(() => {
    if (isAuthenticated) {
      const saved = localStorage.getItem("conversations");
      if (saved) setConversations(JSON.parse(saved));
    }
  }, [isAuthenticated]);

  // Save conversations to localStorage
  useEffect(() => {
    if (isAuthenticated) {
      localStorage.setItem("conversations", JSON.stringify(conversations));
    }
  }, [conversations, isAuthenticated]);

  useLayoutEffect(() => {
    const handleResize = () => {
      setIsShowSidebar(window.innerWidth <= 640);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleNewChat = () => {
    setMessages([]);
    setIsInputCentered(true);
    setCurrentConversationId(null);
    setIsShowSidebar(false);
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

    // Save or update conversation
    let convId = currentConversationId;
    if (!convId) {
      convId = Date.now().toString();
      setCurrentConversationId(convId);
      setConversations((prev) => [
        ...prev,
        {
          id: convId,
          title: userMessage.substring(0, 50),
          messages: updatedMessages,
          createdAt: new Date().toISOString(),
        },
      ]);
    } else {
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === convId ? { ...conv, messages: updatedMessages } : conv
        )
      );
    }

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

      if (!response.ok || !response.body) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      // Read streaming chunks (SSE)
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let displayedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // SSE format → lines start with "data:"
        const lines = chunk
          .split("\n")
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.replace(/^data:\s*/, "").trim());

        for (const line of lines) {
          if (line === "[DONE]") break;

          displayedText += line + " ";

          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: displayedText.trim(),
            };
            return updated;
          });
        }
      }

      // Save final message to conversation
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === convId
            ? {
                ...conv,
                messages: [
                  ...updatedMessages.slice(0, -1),
                  { role: "assistant", content: displayedText.trim() },
                ],
              }
            : conv
        )
      );
    } catch (err) {
      console.error("Chat stream error:", err);
      alert("Error connecting to the assistant.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = (id) => {
    const conversation = conversations.find((c) => c.id === id);
    if (conversation) {
      setMessages(conversation.messages);
      setCurrentConversationId(id);
      setIsInputCentered(false);
      setIsShowSidebar(false);
    }
  };

  const bgColor = isDark ? "#232323" : "#f1f1f1";

  // Show loading spinner while checking auth
  if (authLoading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          backgroundColor: bgColor,
        }}
      >
        <div style={{ color: isDark ? '#ffffff' : '#000000', fontSize: '18px' }}>
          {isArabic ? 'جاري التحميل...' : 'Loading...'}
        </div>
      </div>
    );
  }

  // Show auth screen if not authenticated
  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        backgroundColor: bgColor,
        direction: isArabic ? "rtl" : "ltr",
        transition: "margin 0.3s ease",
        marginLeft: isShowSidebar && !isArabic ? "256px" : "0",
        marginRight: isShowSidebar && isArabic ? "256px" : "0",
      }}
    >
      <Sidebar
        isOpen={isShowSidebar}
        onToggle={() => setIsShowSidebar((prev) => !prev)}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        conversations={conversations}
      />

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          position: "relative",
          transition: "margin 0.3s ease",
        }}
      >
        <button
          onClick={() => setIsShowSidebar(!isShowSidebar)}
          style={{
            position: "absolute",
            top: "16px",
            [isArabic ? "right" : "left"]: "16px",
            zIndex: 20,
            padding: "8px",
            backgroundColor: isDark
              ? "rgba(74, 75, 74, 0.5)"
              : "rgba(229, 229, 229, 0.5)",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            transition: "background-color 0.2s",
          }}
        >
          {isShowSidebar ? (
            <MdOutlineArrowRight
              size={24}
              color={isDark ? "#ffffff" : "#000000"}
            />
          ) : (
            <MdOutlineArrowLeft
              size={24}
              color={isDark ? "#ffffff" : "#000000"}
            />
          )}
        </button>

        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <ChatMessages messages={messages} isLoading={isLoading} />
        )}

        <InputArea
          onSend={handleSendMessage}
          isLoading={isLoading}
          isCentered={isInputCentered && messages.length === 0}
        />
      </div>
    </div>
  );
};

export default App;