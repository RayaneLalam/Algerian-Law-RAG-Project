import React, { useEffect, useRef } from "react";
import { useLanguageTheme } from "../contexts/LanguageThemeContext";
import ReactMarkdown from "react-markdown";

export const ChatMessages = ({ messages, isLoading }) => {
  const { language, theme } = useLanguageTheme();
  const scrollRef = useRef(null);
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const bgColor = isDark ? "#232323" : "#f1f1f1";
  const userMsgBg = isDark ? "#3a3a3a" : "#e8e8e8";
  const userMsgText = isDark ? "#f1f1f1" : "#171717";
  const assistantText = isDark ? "#f1f1f1" : "#171717";
  const borderColor = isDark ? "#4a4b4a" : "#e5e5e5";
  const accentColor = "#D4AF37";
  const codeBlockBg = isDark ? "#2a2a2a" : "#f5f5f5";
  const tableBg = isDark ? "#2a2a2a" : "#f9f9f9";
  const tableHeaderBg = isDark ? "#3a3a3a" : "#e5e5e5";
  const blockquoteBg = isDark ? "#2a2a2a" : "#f9f9f9";
  const blockquoteBorder = accentColor;
  const linkColor = accentColor;
  const secondaryText = isDark ? "#adadad" : "#737373";

  const customMarkdownComponents = {
    strong: ({ children }) => (
      <strong style={{ fontWeight: "700", color: assistantText }}>
        {children}
      </strong>
    ),
    em: ({ children }) => (
      <em style={{ fontStyle: "italic", color: assistantText }}>{children}</em>
    ),
    code: ({ inline, children }) => {
      if (inline) {
        return (
          <code
            style={{
              padding: "2px 6px",
              borderRadius: "4px",
              backgroundColor: codeBlockBg,
              color: accentColor,
              fontSize: "18px",
              fontFamily: "'Courier New', monospace",
            }}
          >
            {children}
          </code>
        );
      }
      return (
        <pre
          style={{
            padding: "12px",
            borderRadius: "8px",
            overflow: "auto",
            margin: "12px 0",
            backgroundColor: codeBlockBg,
            color: assistantText,
            fontFamily: "'Courier New', monospace",
            fontSize: "18px",
            lineHeight: "1.5",
            border: `1px solid ${borderColor}`,
          }}
        >
          <code>{children}</code>
        </pre>
      );
    },
    p: ({ children }) => (
      <p style={{ margin: "8px 0", color: assistantText }}>{children}</p>
    ),
    h1: ({ children }) => (
      <h1
        style={{
          fontSize: "32px",
          fontWeight: "700",
          margin: "24px 0 16px 0",
          color: assistantText,
          lineHeight: "1.2",
        }}
      >
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2
        style={{
          fontSize: "28px",
          fontWeight: "700",
          margin: "20px 0 12px 0",
          color: assistantText,
          lineHeight: "1.3",
        }}
      >
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3
        style={{
          fontSize: "24px",
          fontWeight: "600",
          margin: "16px 0 10px 0",
          color: assistantText,
          lineHeight: "1.4",
        }}
      >
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4
        style={{
          fontSize: "20px",
          fontWeight: "600",
          margin: "14px 0 8px 0",
          color: assistantText,
          lineHeight: "1.4",
        }}
      >
        {children}
      </h4>
    ),
    h5: ({ children }) => (
      <h5
        style={{
          fontSize: "18px",
          fontWeight: "600",
          margin: "12px 0 6px 0",
          color: assistantText,
          lineHeight: "1.5",
        }}
      >
        {children}
      </h5>
    ),
    h6: ({ children }) => (
      <h6
        style={{
          fontSize: "16px",
          fontWeight: "600",
          margin: "10px 0 6px 0",
          color: assistantText,
          lineHeight: "1.5",
        }}
      >
        {children}
      </h6>
    ),
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          color: linkColor,
          textDecoration: "underline",
          transition: "opacity 0.2s",
          cursor: "pointer",
        }}
        onMouseEnter={(e) => (e.target.style.opacity = "0.8")}
        onMouseLeave={(e) => (e.target.style.opacity = "1")}
      >
        {children}
      </a>
    ),
    blockquote: ({ children }) => (
      <blockquote
        style={{
          margin: "16px 0",
          padding: "12px 16px",
          borderLeft: `4px solid ${blockquoteBorder}`,
          backgroundColor: blockquoteBg,
          borderRadius: "4px",
          color: assistantText,
          fontStyle: "italic",
        }}
      >
        {children}
      </blockquote>
    ),
    ul: ({ children }) => (
      <ul
        style={{
          margin: "12px 0",
          paddingLeft: isArabic ? "0" : "24px",
          paddingRight: isArabic ? "24px" : "0",
          color: assistantText,
          listStylePosition: "outside",
        }}
      >
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol
        style={{
          margin: "12px 0",
          paddingLeft: isArabic ? "0" : "24px",
          paddingRight: isArabic ? "24px" : "0",
          color: assistantText,
          listStylePosition: "outside",
        }}
      >
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li
        style={{
          margin: "6px 0",
          color: assistantText,
          lineHeight: "1.6",
        }}
      >
        {children}
      </li>
    ),
    table: ({ children }) => (
      <div style={{ overflowX: "auto", margin: "16px 0" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            backgroundColor: tableBg,
            border: `1px solid ${borderColor}`,
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead
        style={{
          backgroundColor: tableHeaderBg,
          borderBottom: `2px solid ${borderColor}`,
        }}
      >
        {children}
      </thead>
    ),
    tbody: ({ children }) => <tbody>{children}</tbody>,
    tr: ({ children }) => (
      <tr
        style={{
          borderBottom: `1px solid ${borderColor}`,
        }}
      >
        {children}
      </tr>
    ),
    th: ({ children }) => (
      <th
        style={{
          padding: "12px 16px",
          textAlign: isArabic ? "right" : "left",
          fontWeight: "600",
          color: assistantText,
          fontSize: "16px",
        }}
      >
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td
        style={{
          padding: "12px 16px",
          textAlign: isArabic ? "right" : "left",
          color: assistantText,
          fontSize: "16px",
        }}
      >
        {children}
      </td>
    ),
    hr: () => (
      <hr
        style={{
          margin: "20px 0",
          border: "none",
          borderTop: `1px solid ${borderColor}`,
        }}
      />
    ),
    img: ({ src, alt }) => (
      <img
        src={src}
        alt={alt}
        style={{
          maxWidth: "100%",
          height: "auto",
          borderRadius: "8px",
          margin: "12px 0",
          border: `1px solid ${borderColor}`,
        }}
      />
    ),
    del: ({ children }) => (
      <del
        style={{
          color: secondaryText,
          textDecoration: "line-through",
        }}
      >
        {children}
      </del>
    ),
  };

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        backgroundColor: bgColor,
      }}
    >
      <div
        style={{
          maxWidth: "1000px",
          margin: "0 auto",
          width: "100%",
          padding: "32px 16px",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: "32px",
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              direction: isArabic ? "rtl" : "ltr",
            }}
            ref={idx === messages.length - 1 ? scrollRef : null}
          >
            <div
              style={{
                maxWidth: "600px",
                padding: msg.role === "user" ? "12px 16px" : "0",
                backgroundColor:
                  msg.role === "user" ? userMsgBg : "transparent",
                borderRadius: msg.role === "user" ? "16px" : "0",
              }}
            >
              {msg.role === "user" ? (
                <p
                  style={{
                    fontSize: "18px",
                    lineHeight: "1.6",
                    color: userMsgText,
                    fontWeight: "500",
                    margin: 0,
                  }}
                >
                  {msg.content}
                </p>
              ) : (
                <div
                  style={{
                    fontSize: "18px",
                    lineHeight: "1.6",
                    color: assistantText,
                  }}
                >
                  <ReactMarkdown components={customMarkdownComponents}>
                    {msg.content}
                  </ReactMarkdown>
                  {isLoading && idx === messages.length - 1 && (
                    <span
                      style={{
                        marginLeft: "4px",
                        display: "inline-block",
                        width: "8px",
                        height: "20px",
                        backgroundColor: accentColor,
                        borderRadius: "2px",
                        animation: "pulse 2s ease-in-out infinite",
                      }}
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};
