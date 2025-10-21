import React, { useState, useEffect, useLayoutEffect } from "react";
import { useLanguageTheme } from "./contexts/LanguageThemeContext";
import { Sidebar } from "./components/Sidebar";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import { ChatMessages } from "./components/ChatMessages";
import { InputArea } from "./components/InputArea";
import { MdOutlineArrowLeft, MdOutlineArrowRight } from "react-icons/md";

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

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    const dummyResponse = isArabic
      ? `**إجابتي هي:**  

أنا **Konan.ai**، مساعد ذكاء اصطناعي متخصص في **القانون الجزائري**.  
يمكنني مساعدتك في:  

- **شرح النصوص القانونية**  
- **تلخيص القوانين والمراسيم**  
- **ترجمة المواد بين العربية والفرنسية**  
- **تقديم إجابات مدعومة بالمراجع القانونية**  

ما هو النص أو السؤال القانوني الذي ترغب في فهمه؟`
      : `**Voici ma réponse :**  

Je suis **Konan.ai**, un assistant IA spécialisé dans **le droit algérien**.  
Je peux vous aider à :  

- **Expliquer les textes juridiques**  
- **Résumer les lois et décrets**  
- **Traduire les articles entre l’arabe et le français**  
- **Fournir des réponses basées sur des sources juridiques fiables**  

Quel texte ou quelle question juridique souhaitez-vous comprendre ?`;

    let displayedText = "";
    const words = dummyResponse.split(" ");

    for (let i = 0; i < words.length; i++) {
      displayedText += words[i] + (i < words.length - 1 ? " " : "");

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: displayedText,
        };
        return updated;
      });

      await new Promise((resolve) => setTimeout(resolve, 20));
    }

    // Update conversation with final assistant message
    if (currentConversationId) {
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === currentConversationId
            ? {
                ...conv,
                messages: [
                  ...updatedMessages.slice(0, -1),
                  { role: "assistant", content: dummyResponse },
                ],
              }
            : conv
        )
      );
    }

    setIsLoading(false);
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
        transition: "margin 0.3s ease", // smooth animation
        marginLeft: isShowSidebar && !isArabic ? "256px" : "0", // sidebar width = 256px
        marginRight: isShowSidebar && isArabic ? "256px" : "0",
      }}
    >
      {/* Sidebar */}
      <Sidebar
        isOpen={isShowSidebar}
        onToggle={() => setIsShowSidebar((prev) => !prev)}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        conversations={conversations}
      />

      {/* Main Chat */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          position: "relative",
          transition: "margin 0.3s ease",
        }}
      >
        {/* Toggle Button */}
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

        {/* Messages or Welcome */}
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <ChatMessages messages={messages} isLoading={isLoading} />
        )}

        {/* Input Area */}
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
