import React, { useState, useEffect, useLayoutEffect } from "react";
import { useLanguageTheme } from "./contexts/LanguageThemeContext";
import { Sidebar } from "./components/Sidebar";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import { ChatMessages } from "./components/ChatMessages";
import { InputArea } from "./components/InputArea";
import { MdOutlineArrowLeft, MdOutlineArrowRight } from "react-icons/md";
import { apiClient } from "./services/apiClient";

export const App = () => {
  const { language, theme } = useLanguageTheme();
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
    const saved = localStorage.getItem("conversations");
    if (saved) setConversations(JSON.parse(saved));
  }, []);

  // Save conversations to localStorage
  useEffect(() => {
    localStorage.setItem("conversations", JSON.stringify(conversations));
  }, [conversations]);

  const handleSendMessage = async (text, queryLanguage = "auto") => {
    if (!text.trim() || isLoading) return;

    setIsInputCentered(false);
    setIsLoading(true);

    const userMessage = text;
    const updatedMessages = [
      ...messages,
      { role: "user", content: userMessage },
      { role: "assistant", content: "", language: queryLanguage },
    ];
    setMessages(updatedMessages);

    // Save or update conversation
    if (!currentConversationId) {
      const newId = Date.now().toString();
      setCurrentConversationId(newId);
      setConversations((prev) => [
        ...prev,
        {
          id: newId,
          title: userMessage.substring(0, 50),
          messages: updatedMessages,
          createdAt: new Date().toISOString(),
        },
      ]);
    } else {
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === currentConversationId
            ? { ...conv, messages: updatedMessages }
            : conv
        )
      );
    }

    try {
      // Get JWT token from localStorage
      const token = localStorage.getItem("authToken") || "";

      // Call the actual API
      const response = await apiClient.chatStream(
        userMessage,
        currentConversationId,
        queryLanguage,
        token
      );

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let displayedText = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.chunk) {
                  displayedText += data.chunk;
                  setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      content: displayedText,
                    };
                    return updated;
                  });
                }
              } catch (e) {
                // Ignore JSON parse errors
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Update conversation with final message
      if (currentConversationId) {
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === currentConversationId
              ? {
                  ...conv,
                  messages: [
                    ...updatedMessages.slice(0, -1),
                    { role: "assistant", content: displayedText, language: queryLanguage },
                  ],
                }
              : conv
          )
        );
      }
    } catch (error) {
      console.error("Error calling API:", error);
      const errorMessage = error.message || "Error communicating with server";
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: `Error: ${errorMessage}. Make sure backend is running at http://localhost:5000`,
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setIsInputCentered(true);
    setIsShowSidebar(false);
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

  useLayoutEffect(() => {
    const handleResize = () => {
      setIsShowSidebar(window.innerWidth <= 640);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const bgColor = isDark ? "#232323" : "#f1f1f1";

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
