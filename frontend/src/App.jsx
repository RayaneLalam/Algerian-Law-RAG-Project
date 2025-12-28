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

  // Load conversations from backend
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchConversations();
    }
  }, [isAuthenticated, token]);

  const fetchConversations = async () => {
    setConversationsLoading(true);
    try {
      const response = await fetch("http://localhost:5000/conversations", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      } else {
        console.error("Failed to fetch conversations");
      }
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setConversationsLoading(false);
    }
  };

  const fetchConversationMessages = async (conversationId) => {
    try {
      const response = await fetch(
        `http://localhost:5000/conversations/${conversationId}/messages`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Convert backend message format to frontend format
        const formattedMessages = data.messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));
        return formattedMessages;
      } else {
        console.error("Failed to fetch messages");
        return [];
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
      return [];
    }
  };

  useLayoutEffect(() => {
    const handleResize = () => {
      // Auto-open sidebar on larger screens
      setIsShowSidebar(window.innerWidth > 640);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleNewChat = () => {
    setMessages([]);
    setIsInputCentered(true);
    setCurrentConversationId(null);
    // Don't close sidebar on desktop
    if (window.innerWidth <= 640) {
      setIsShowSidebar(false);
    }
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

      // Update final message
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: displayedText.trim(),
        };
        return updated;
      });

      // Refresh conversations list to get updated conversation
      await fetchConversations();

      // If this was a new conversation, get the conversation ID from the response header or refetch
      if (!currentConversationId) {
        // The backend creates a conversation, so we need to find it
        // For now, we'll just refresh the list and the newest one will be at the top
        const convResponse = await fetch("http://localhost:5000/conversations", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (convResponse.ok) {
          const data = await convResponse.json();
          if (data.conversations && data.conversations.length > 0) {
            // Set the most recent conversation as current
            setCurrentConversationId(parseInt(data.conversations[0].id));
          }
        }
      }

    } catch (err) {
      console.error("Chat stream error:", err);
      alert("Error connecting to the assistant.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = async (id) => {
    const conversationId = parseInt(id);
    setCurrentConversationId(conversationId);
    setIsInputCentered(false);
    
    // Fetch messages for this conversation
    const conversationMessages = await fetchConversationMessages(conversationId);
    setMessages(conversationMessages);
    
    // Close sidebar on mobile after selection
    if (window.innerWidth <= 640) {
      setIsShowSidebar(false);
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      const response = await fetch(
        `http://localhost:5000/conversations/${id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        // If we deleted the current conversation, start a new chat
        if (currentConversationId === parseInt(id)) {
          handleNewChat();
        }
        // Refresh conversations list
        await fetchConversations();
      } else {
        console.error("Failed to delete conversation");
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
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
        width: "100vw", // Ensure it fills width
        backgroundColor: bgColor,
        direction: isArabic ? "rtl" : "ltr",
        overflow: "hidden", // FIX: Prevents the outer scrollbar
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

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          position: "relative",
          height: "100vh", // FIX: Keep the content area strictly at viewport height
          marginLeft: isShowSidebar && !isArabic ? "256px" : "0",
          marginRight: isShowSidebar && isArabic ? "256px" : "0",
          transition: "margin 0.3s ease",
          overflow: "hidden", // FIX: Prevents this container from expanding
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
            isArabic ? (
              <MdOutlineArrowRight
                size={24}
                color={isDark ? "#ffffff" : "#000000"}
              />
            ) : (
              <MdOutlineArrowLeft
                size={24}
                color={isDark ? "#ffffff" : "#000000"}
              />
            )
          ) : isArabic ? (
            <MdOutlineArrowLeft
              size={24}
              color={isDark ? "#ffffff" : "#000000"}
            />
          ) : (
            <MdOutlineArrowRight
              size={24}
              color={isDark ? "#ffffff" : "#000000"}
            />
          )}
        </button>

        <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          {messages.length === 0 ? (
            <div style={{ flex: 1, overflowY: "auto" }}>
              <WelcomeScreen />
            </div>
          ) : (
            <ChatMessages messages={messages} isLoading={isLoading} />
          )}
        </div>

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