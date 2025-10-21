import React from "react";
import { useLanguageTheme } from "../contexts/LanguageThemeContext";
import { MdLanguage, MdLogout } from "react-icons/md";
import { BsSun, BsMoon } from "react-icons/bs";
import { IoMdHelpCircle } from "react-icons/io";
import { HiOutlineMenuAlt2 } from "react-icons/hi"; // new menu icon

export const Sidebar = ({
  isOpen,
  onToggle,
  onNewChat,
  onSelectConversation,
  conversations,
}) => {
  const { language, theme, toggleLanguage, toggleTheme, t } =
    useLanguageTheme();
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  const bgColor = isDark ? "#232323" : "#f1f1f1";
  const textColor = isDark ? "#ffffff" : "#1c1c1c";
  const secondaryText = isDark ? "#adadad" : "#6b6b6b";
  const borderColor = isDark ? "#4a4b4a" : "#e5e5e5";
  const hoverBg = isDark ? "#3a3a3a" : "#f0f0f0";
  const accentColor = "#D4AF37";

  return (
    <div
      className={`absolute inset-y-0 w-64 transition-transform duration-300 z-40 flex flex-col border-r ${
        isOpen
          ? "translate-x-0"
          : isArabic
            ? "translate-x-full"
            : "-translate-x-full"
      }`}
      style={{
        backgroundColor: isDark ? "#232323" : "#f1f1f1",
        borderColor: isDark ? "#4a4b4a" : "#e5e5e5",
        fontFamily: isArabic ? '"Cairo", sans-serif' : '"Inter", sans-serif',
        [isArabic ? "borderLeft" : "borderRight"]: `1px solid ${
          isDark ? "#4a4b4a" : "#e5e5e5"
        }`,
        right: isArabic ? 0 : "auto",
        left: isArabic ? "auto" : 0,
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
          onClick={onToggle} // <-- important
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
        {conversations.length === 0 ? (
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
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => {
                onSelectConversation(conv.id);
                onToggle();
              }}
              style={{
                padding: "8px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "18px",
                color: textColor,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                transition: "background-color 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = hoverBg)
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = "transparent")
              }
            >
              {conv.title}
            </div>
          ))
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
