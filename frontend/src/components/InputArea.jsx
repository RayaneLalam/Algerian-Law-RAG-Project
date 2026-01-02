import React, { useState } from "react";
import { useLanguageTheme } from "../contexts/LanguageThemeContext";
import { BiSend } from "react-icons/bi";
import { MdLanguage } from "react-icons/md";

export const InputArea = ({ onSend, isLoading, isCentered }) => {
  const [text, setText] = useState("");
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const { language, theme, t, queryLanguage, setQueryLanguagePreference } = useLanguageTheme();
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  const bgColor = isDark ? "#232323" : "#f1f1f1";
  const inputBg = isDark ? "#2a2a2a" : "#f9f9f9";
  const textColor = isDark ? "#ffffff" : "#171717";
  const borderColor = isDark ? "#4a4b4a" : "#e5e5e5";
  const accentColor = "#D4AF37";
  const secondaryText = isDark ? "#adadad" : "#737373";

  const handleSubmit = () => {
    if (text.trim() && !isLoading) {
      onSend(text, queryLanguage);
      setText("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleLanguageSelect = (lang) => {
    setQueryLanguagePreference(lang);
    setShowLanguageMenu(false);
  };

  return (
    <div
      style={{
        borderTop: "none",
        backgroundColor: isCentered ? "transparent" : bgColor,
        position: isCentered ? "absolute" : "relative",
        top: isCentered ? "40%" : "auto",
        left: isCentered ? "50%" : "auto",
        transform: isCentered ? "translate(-50%, -50%)" : "none",
        width: isCentered ? "100%" : "auto",
        maxWidth: isCentered ? "600px" : "none",
        transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
        zIndex: isCentered ? 10 : 1,
      }}
    >
      <div
        style={{
          maxWidth: "1000px",
          margin: "0 auto",
          width: "100%",
          padding: isCentered ? "0 16px" : "24px 16px",
        }}
      >
        {!isCentered && (
          <div
            style={{
              marginBottom: "12px",
              display: "flex",
              gap: "8px",
              direction: isArabic ? "rtl" : "ltr",
              alignItems: "center",
            }}
          >
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setShowLanguageMenu(!showLanguageMenu)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  backgroundColor: inputBg,
                  border: `1px solid ${borderColor}`,
                  borderRadius: "4px",
                  color: textColor,
                  fontSize: "12px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = accentColor;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = borderColor;
                }}
              >
                <MdLanguage size={14} />
                {queryLanguage === "auto"
                  ? t.detectLanguage
                  : queryLanguage === "ar"
                    ? t.arabic
                    : t.french}
              </button>
              {showLanguageMenu && (
                <div
                  style={{
                    position: "absolute",
                    top: "100%",
                    left: isArabic ? "auto" : "0",
                    right: isArabic ? "0" : "auto",
                    marginTop: "4px",
                    backgroundColor: inputBg,
                    border: `1px solid ${borderColor}`,
                    borderRadius: "4px",
                    zIndex: 100,
                    minWidth: "120px",
                  }}
                >
                  {["auto", "fr", "ar"].map((lang) => (
                    <button
                      key={lang}
                      onClick={() => handleLanguageSelect(lang)}
                      style={{
                        display: "block",
                        width: "100%",
                        padding: "8px 12px",
                        backgroundColor:
                          queryLanguage === lang ? accentColor : "transparent",
                        color: queryLanguage === lang ? "#000" : textColor,
                        border: "none",
                        textAlign: isArabic ? "right" : "left",
                        cursor: "pointer",
                        fontSize: "12px",
                        transition: "all 0.2s",
                      }}
                      onMouseEnter={(e) => {
                        if (queryLanguage !== lang) {
                          e.currentTarget.style.backgroundColor = isDark
                            ? "#3a3a3a"
                            : "#f0f0f0";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (queryLanguage !== lang) {
                          e.currentTarget.style.backgroundColor = "transparent";
                        }
                      }}
                    >
                      {lang === "auto"
                        ? t.detectLanguage
                        : lang === "ar"
                          ? t.arabic
                          : t.french}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        <div
          style={{
            display: "flex",
            gap: "12px",
            direction: isArabic ? "rtl" : "ltr",
          }}
        >
          <input
            type="text"
            placeholder={t.example}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            autoFocus={isCentered}
            style={{
              flex: 1,
              backgroundColor: inputBg,
              borderRadius: "4px",
              padding: "14px 20px",
              border: `1px solid ${borderColor}`,
              color: textColor,
              fontSize: isCentered ? "13px" : "14px",
              fontWeight: "200",
              outline: "none",
              opacity: isLoading ? 0.5 : 1,
              transition:
                "border-color 0.2s, background-color 0.2s, font-size 0.3s",
              fontFamily: isArabic ? "Cairo" : "Inter",
            }}
            onFocus={(e) => (e.target.style.borderColor = accentColor)}
            onBlur={(e) => (e.target.style.borderColor = borderColor)}
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !text.trim()}
            style={{
              backgroundColor: inputBg,
              border: `1px solid ${borderColor}`,
              padding: "12px 12px",
              borderRadius: "4px",
              cursor: isLoading || !text.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: isLoading || !text.trim() ? 0.5 : 1,
              transition: "background-color 0.2s, border-color 0.2s",
            }}
            onMouseEnter={(e) => {
              if (!isLoading && text.trim()) {
                e.currentTarget.style.backgroundColor = isDark
                  ? "#3a3a3a"
                  : "#f0f0f0";
                e.currentTarget.style.borderColor = accentColor;
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = inputBg;
              e.currentTarget.style.borderColor = borderColor;
            }}
          >
            {isArabic ? (
              <BiSend
                size={18}
                style={{
                  color: accentColor,
                  transform: "scaleX(-1)",
                }}
              />
            ) : (
              <BiSend size={18} style={{ color: accentColor }} />
            )}
          </button>
        </div>
        {!isCentered && (
          <p
            style={{
              fontSize: "12px",
              color: secondaryText,
              marginTop: "12px",
              textAlign: "center",
              margin: "12px 0 0 0",
            }}
          >
            {t.disclaimer}
          </p>
        )}
      </div>
    </div>
  );
};
