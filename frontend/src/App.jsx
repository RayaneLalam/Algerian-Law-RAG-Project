import React, { useState, useEffect, useLayoutEffect } from "react";
import { useLanguageTheme } from "./contexts/LanguageThemeContext";
import { useAuth } from "./contexts/AuthContext";
import { Sidebar } from "./components/Sidebar";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import { ChatMessages } from "./components/ChatMessages";
import { InputArea } from "./components/InputArea";
import { AuthScreen } from "./components/AuthScreen";
import { HiOutlineMenuAlt2 } from "react-icons/hi";
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
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);

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
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: displayedText.trim(),
            };
            return updated;
          });
        }
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: displayedText.trim(),
        };
        return updated;
      });

      await fetchConversations();

      if (!currentConversationId) {
        const convResponse = await fetch(
          "http://localhost:5000/conversations",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        if (convResponse.ok) {
          const data = await convResponse.json();
          if (data.conversations && data.conversations.length > 0) {
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

    const conversationMessages =
      await fetchConversationMessages(conversationId);
    setMessages(conversationMessages);

    if (window.innerWidth <= 640) {
      setIsShowSidebar(false);
    }
  };

  const handleDeleteConversation = async (id) => {
    setConversationToDelete(id);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!conversationToDelete) return;

    try {
      const response = await fetch(
        `http://localhost:5000/conversations/${conversationToDelete}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        if (currentConversationId === parseInt(conversationToDelete)) {
          handleNewChat();
        }
        await fetchConversations();
      } else {
        console.error("Failed to delete conversation");
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    } finally {
      setShowDeleteModal(false);
      setConversationToDelete(null);
    }
  };

  const cancelDelete = () => {
    setShowDeleteModal(false);
    setConversationToDelete(null);
  };

  const bgColor = isDark ? "#232323" : "#f1f1f1";

  if (authLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          backgroundColor: bgColor,
          fontFamily: isArabic ? '"Cairo", sans-serif' : '"Inter", sans-serif',
        }}
      >
        <div
          style={{ color: isDark ? "#ffffff" : "#000000", fontSize: "18px" }}
        >
          {isArabic ? "جاري التحميل..." : "Chargement..."}
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        backgroundColor: bgColor,
        fontFamily: isArabic ? '"Cairo", sans-serif' : '"Inter", sans-serif',
        overflow: "hidden",
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      }}
    >
      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 50,
            backdropFilter: "blur(4px)",
          }}
          onClick={cancelDelete}
        >
          <div
            style={{
              backgroundColor: isDark ? "#2a2a2a" : "#ffffff",
              borderRadius: "12px",
              padding: "24px",
              maxWidth: "400px",
              width: "90%",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2)",
              fontFamily: isArabic
                ? '"Cairo", sans-serif'
                : '"Inter", sans-serif',
              direction: isArabic ? "rtl" : "ltr",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                fontSize: "20px",
                fontWeight: "600",
                color: isDark ? "#ffffff" : "#1c1c1c",
                marginBottom: "12px",
              }}
            >
              {isArabic ? "تأكيد الحذف" : "Confirmer la suppression"}
            </h3>
            <p
              style={{
                fontSize: "16px",
                color: isDark ? "#adadad" : "#6b6b6b",
                marginBottom: "24px",
                lineHeight: "1.5",
              }}
            >
              {isArabic
                ? "هل أنت متأكد من أنك تريد حذف هذه المحادثة؟ لا يمكن التراجع عن هذا الإجراء."
                : "Êtes-vous sûr de vouloir supprimer cette conversation ? Cette action ne peut pas être annulée."}
            </p>
            <div
              style={{
                display: "flex",
                gap: "12px",
                justifyContent: "flex-end",
              }}
            >
              <button
                onClick={cancelDelete}
                style={{
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: `1px solid ${isDark ? "#4a4b4a" : "#e5e5e5"}`,
                  backgroundColor: "transparent",
                  color: isDark ? "#ffffff" : "#1c1c1c",
                  cursor: "pointer",
                  fontSize: "16px",
                  fontWeight: "500",
                  transition: "background-color 0.2s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = isDark
                    ? "#3a3a3a"
                    : "#f0f0f0")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                {isArabic ? "إلغاء" : "Annuler"}
              </button>
              <button
                onClick={confirmDelete}
                style={{
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "none",
                  backgroundColor: "#ef4444",
                  color: "#ffffff",
                  cursor: "pointer",
                  fontSize: "16px",
                  fontWeight: "500",
                  transition: "background-color 0.2s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#dc2626")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "#ef4444")
                }
              >
                {isArabic ? "حذف" : "Supprimer"}
              </button>
            </div>
          </div>
        </div>
      )}

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
          height: "100vh",
          transition: "margin 0.3s ease",
          marginLeft:
            isShowSidebar && !isArabic && window.innerWidth > 640
              ? "256px"
              : "0",
          marginRight:
            isShowSidebar && isArabic && window.innerWidth > 640
              ? "256px"
              : "0",
          direction: isArabic ? "rtl" : "ltr",
        }}
      >
        {/* Floating toggle button - shows when sidebar is closed */}
        {!isShowSidebar && (
          <button
            onClick={() => setIsShowSidebar(true)}
            style={{
              position: "absolute",
              top: "16px",
              [isArabic ? "right" : "left"]: "16px",
              zIndex: 30,
              width: "40px",
              height: "40px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              backgroundColor: isDark ? "#4a4b4a" : "#e5e5e5",
              color: isDark ? "#ffffff" : "#1c1c1c",
              transition: "background-color 0.2s",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.backgroundColor = isDark
                ? "#5a5b5a"
                : "#d4d4d4")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.backgroundColor = isDark
                ? "#4a4b4a"
                : "#e5e5e5")
            }
          >
            <HiOutlineMenuAlt2 size={20} />
          </button>
        )}

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
