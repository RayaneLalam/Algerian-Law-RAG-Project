import React from "react";
import { useLanguageTheme } from "../contexts/LanguageThemeContext";
import { MdLanguage, MdLogout, MdDelete } from "react-icons/md";
import { BsSun, BsMoon } from "react-icons/bs";
import { IoMdHelpCircle } from "react-icons/io";
import { HiOutlineMenuAlt2 } from "react-icons/hi";

export const Sidebar = ({
  isOpen,
  onToggle,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  conversations,
  conversationsLoading,
  currentConversationId,
}) => {
  const { language, theme, toggleLanguage, toggleTheme, t } =
    useLanguageTheme();
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  const textColor = isDark ? "#ffffff" : "#1c1c1c";
  const secondaryText = isDark ? "#adadad" : "#6b6b6b";
  const borderColor = isDark ? "#4a4b4a" : "#e5e5e5";
  const hoverBg = isDark ? "#3a3a3a" : "#f0f0f0";
  const activeBg = isDark ? "#4a4b4a" : "#e5e5e5";

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        bottom: 0,
        [isArabic ? "right" : "left"]: 0,
        width: "256px",
        backgroundColor: isDark ? "#232323" : "#f1f1f1",
        borderRight: isArabic ? "none" : `1px solid ${borderColor}`,
        borderLeft: isArabic ? `1px solid ${borderColor}` : "none",
        fontFamily: isArabic ? '"Cairo", sans-serif' : '"Inter", sans-serif',
        display: "flex",
        flexDirection: "column",
        transform: isOpen ? "translateX(0)" : isArabic ? "translateX(100%)" : "translateX(-100%)",
        transition: "transform 0.3s ease",
        zIndex: 40,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <img
          alt="logo"
          src="\gold_logo.svg"
          width={40}
          onClick={onNewChat}
          style={{ cursor: "pointer" }}
        />

        {/* Sidebar Toggle */}
        <button
          onClick={onToggle}
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            backgroundColor: isDark ? "#4a4b4a" : "#e5e5e5",
            color: isDark ? "#ffffff" : "#1c1c1c",
            transition: "background-color 0.2s",
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
      </div>

      {/* New Chat Button */}
      <button
        onClick={onNewChat}
        style={{
          width: "calc(100% - 32px)",
          margin: "0 16px 16px",
          padding: "10px 16px",
          borderRadius: "8px",
          backgroundColor: "transparent",
          color: textColor,
          border: `1px solid ${borderColor}`,
          cursor: "pointer",
          fontWeight: "400",
          fontSize: "16px",
          display: "flex",
          gap: "8px",
          transition: "background-color 0.2s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = hoverBg)}
        onMouseLeave={(e) =>
          (e.currentTarget.style.backgroundColor = "transparent")
        }
      >
        <span>+</span>
        <span>{t.newChat}</span>
      </button>

      {/* Conversations */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0 16px 16px",
        }}
      >
        <p
          style={{
            fontSize: "13px",
            fontWeight: "600",
            color: secondaryText,
            marginBottom: "12px",
          }}
        >
          {t.recent}
        </p>
        
        {conversationsLoading ? (
          <p
            style={{
              fontSize: "16px",
              color: secondaryText,
              padding: "12px",
              textAlign: "center",
            }}
          >
            {isArabic ? "جاري التحميل..." : "Chargement..."}
          </p>
        ) : conversations.length === 0 ? (
          <p
            style={{
              fontSize: "16px",
              color: secondaryText,
              padding: "12px",
              textAlign: "center",
            }}
          >
            {isArabic ? "لا توجد محادثات" : "Aucune conversation"}
          </p>
        ) : (
          conversations.map((conv) => {
            const isActive = currentConversationId === parseInt(conv.id);
            return (
              <div
                key={conv.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "18px",
                  color: textColor,
                  backgroundColor: isActive ? activeBg : "transparent",
                  transition: "background-color 0.2s",
                  marginBottom: "4px",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = hoverBg;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = "transparent";
                  }
                }}
              >
                <div
                  onClick={() => onSelectConversation(conv.id)}
                  style={{
                    flex: 1,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {conv.title}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm(
                      isArabic 
                        ? "هل تريد حذف هذه المحادثة؟" 
                        : "Supprimer cette conversation?"
                    )) {
                      onDeleteConversation(conv.id);
                    }
                  }}
                  style={{
                    padding: "4px",
                    borderRadius: "4px",
                    border: "none",
                    backgroundColor: "transparent",
                    color: secondaryText,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = isDark 
                      ? "rgba(239, 68, 68, 0.2)" 
                      : "rgba(239, 68, 68, 0.1)";
                    e.currentTarget.style.color = "#ef4444";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "transparent";
                    e.currentTarget.style.color = secondaryText;
                  }}
                >
                  <MdDelete size={16} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Settings */}
      <div
        style={{
          borderTop: `1px solid ${borderColor}`,
          padding: "12px",
          display: "flex",
          flexDirection: "column",
          gap: "4px",
        }}
      >
        {/* Language */}
        <button
          onClick={toggleLanguage}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: "transparent",
            color: textColor,
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = hoverBg)
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "transparent")
          }
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              fontFamily: isArabic
                ? '"Cairo", sans-serif'
                : '"Inter", sans-serif',
              fontWeight: "400",
            }}
          >
            <MdLanguage size={16} style={{ color: textColor }} />
            <span>{t.language}</span>
          </div>
        </button>

        {/* Theme */}
        <button
          onClick={toggleTheme}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: "transparent",
            color: textColor,
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = hoverBg)
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "transparent")
          }
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              fontFamily: isArabic
                ? '"Cairo", sans-serif'
                : '"Inter", sans-serif',
              fontWeight: "400",
            }}
          >
            {theme === "dark" ? (
              <BsSun size={16} style={{ color: textColor }} />
            ) : (
              <BsMoon size={16} style={{ color: textColor }} />
            )}
            <span>{theme === "dark" ? t.lightMode : t.darkMode}</span>
          </div>
        </button>

        {/* Updates */}
        <button
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "12px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: "transparent",
            color: textColor,
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "400",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = hoverBg)
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "transparent")
          }
        >
          <IoMdHelpCircle size={16} style={{ color: textColor }} />
          <span>{t.updates}</span>
        </button>

        {/* Logout */}
        <button
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "12px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: "transparent",
            color: "#ef4444",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "500",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.1)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "transparent")
          }
        >
          <MdLogout size={16} />
          <span>{t.logout}</span>
        </button>
      </div>
    </div>
  );
};