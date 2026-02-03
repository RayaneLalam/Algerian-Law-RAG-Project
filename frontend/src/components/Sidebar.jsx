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
  const { language, theme, toggleLanguage, toggleTheme, t } = useLanguageTheme();
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  const textColor = isDark ? "#ffffff" : "#1c1c1c";
  const secondaryText = isDark ? "#adadad" : "#6b6b6b";
  const borderColor = isDark ? "#4a4b4a" : "#e5e5e5";
  const hoverBg = isDark ? "#3a3a3a" : "#f0f0f0";
  const activeBg = isDark ? "#4a4b4a" : "#e5e5e5";

  const isMobile = window.innerWidth <= 768;

  return (
    <aside
      style={{
        width: isOpen ? "260px" : "0px",
        height: "100%",
        backgroundColor: isDark ? "#232323" : "#f1f1f1",
        borderRight: !isArabic && isOpen ? `1px solid ${borderColor}` : "none",
        borderLeft: isArabic && isOpen ? `1px solid ${borderColor}` : "none",
        display: "flex",
        flexDirection: "column",
        transition: "width 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        overflow: "hidden",
        position: isMobile ? "fixed" : "relative",
        top: 0,
        [isArabic ? "right" : "left"]: 0,
        zIndex: 40,
        visibility: isOpen ? "visible" : "hidden",
      }}
    >
      <div style={{ width: "260px", height: "100%", display: "flex", flexDirection: "column" }}>
        {/* Header */}
        <div style={{ padding: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <img alt="logo" src="/gold_logo.svg" width={40} onClick={onNewChat} style={{ cursor: "pointer" }} />
          <button
            onClick={onToggle}
            style={{
              width: "32px", height: "32px", borderRadius: "8px", border: "none", cursor: "pointer",
              display: "flex", justifyContent: "center", alignItems: "center",
              backgroundColor: isDark ? "#4a4b4a" : "#e5e5e5", color: textColor
            }}
          >
            <HiOutlineMenuAlt2 size={20} />
          </button>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          style={{
            width: "calc(100% - 32px)", margin: "0 16px 16px", padding: "10px 16px",
            borderRadius: "8px", backgroundColor: "transparent", color: textColor,
            border: `1px solid ${borderColor}`, cursor: "pointer", display: "flex", gap: "8px"
          }}
        >
          <span>+</span>
          <span style={{ whiteSpace: "nowrap" }}>{t.newChat}</span>
        </button>

        {/* Conversations Area - scrollable */}
        <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "0 16px 16px" }}>
          <p style={{ fontSize: "13px", fontWeight: "600", color: secondaryText, marginBottom: "12px" }}>
            {t.recent}
          </p>
          
          {conversationsLoading ? (
            <p style={{ color: secondaryText, textAlign: "center" }}>...</p>
          ) : (
            conversations.map((conv) => {
              const isActive = currentConversationId === parseInt(conv.id);
              return (
                <div
                  key={conv.id}
                  style={{
                    display: "flex", alignItems: "center", gap: "8px", padding: "8px",
                    borderRadius: "8px", cursor: "pointer", color: textColor,
                    backgroundColor: isActive ? activeBg : "transparent", marginBottom: "4px"
                  }}
                >
                  <div
                    onClick={() => onSelectConversation(conv.id)}
                    style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                  >
                    {conv.title}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm(isArabic ? "حذف؟" : "Delete?")) onDeleteConversation(conv.id);
                    }}
                    style={{ background: "transparent", border: "none", color: secondaryText, cursor: "pointer" }}
                  >
                    <MdDelete size={16} />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Settings - Footer area */}
        <div style={{ borderTop: `1px solid ${borderColor}`, padding: "12px", gap: "4px", display: "flex", flexDirection: "column" }}>
          <SettingBtn icon={<MdLanguage size={16} />} text={t.language} onClick={toggleLanguage} color={textColor} />
          <SettingBtn 
            icon={theme === "dark" ? <BsSun size={16} /> : <BsMoon size={16} />} 
            text={theme === "dark" ? t.lightMode : t.darkMode} 
            onClick={toggleTheme} 
            color={textColor} 
          />
          <SettingBtn icon={<IoMdHelpCircle size={16} />} text={t.updates} color={textColor} />
          <SettingBtn icon={<MdLogout size={16} />} text={t.logout} color="#ef4444" />
        </div>
      </div>
    </aside>
  );
};

// Small helper component for sidebar buttons to keep code clean
const SettingBtn = ({ icon, text, onClick, color }) => (
  <button
    onClick={onClick}
    style={{
      width: "100%", display: "flex", alignItems: "center", gap: "10px", padding: "10px",
      borderRadius: "8px", border: "none", backgroundColor: "transparent",
      color: color, cursor: "pointer", fontSize: "14px", transition: "background 0.2s"
    }}
    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "rgba(150,150,150,0.1)"}
    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}
  >
    {icon}
    <span style={{ whiteSpace: "nowrap" }}>{text}</span>
  </button>
);