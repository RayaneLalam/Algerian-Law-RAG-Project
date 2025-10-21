import React from "react";
import { useLanguageTheme } from "../contexts/LanguageThemeContext";
import { MdOutlineBalance, MdLanguage, MdSmartToy } from "react-icons/md";

export const WelcomeScreen = () => {
  const { language, theme, t } = useLanguageTheme();
  const isArabic = language === "ar";
  const isDark = theme === "dark";

  const bgColor = isDark ? "#232323" : "#f1f1f1";
  const textColor = isDark ? "#ffffff" : "#1c1c1c";
  const secondaryText = isDark ? "#adadad" : "#6b6b6b";
  const accentColor = "#D4AF37";

  const features = [
    {
      icon: <MdOutlineBalance size={32} />,
      title: t.reliableSources,
      description: t.reliableSourcesDesc,
    },
    {
      icon: <MdLanguage size={32} />,
      title: t.bilingualExplanations,
      description: t.bilingualExplanationsDesc,
    },
    {
      icon: <MdSmartToy size={32} />,
      title: t.intelligentAnalysis,
      description: t.intelligentAnalysisDesc,
    },
  ];

  return (
    <div
      className="welcome-bg"
      style={{
        flex: 1,
        overflowY: "auto",
        background: isDark
          ? "radial-gradient(ellipse at center bottom, rgba(212,175,55,0.3) 0%, rgba(212,175,55,0.1) 25%, #232323 60%)"
          : "radial-gradient(ellipse at center bottom, rgba(212,175,55,0.4) 0%, rgba(212,175,55,0.15) 25%, #f1f1f1 60%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* Main Heading */}
      <div
        style={{
          textAlign: "center",
          marginBottom: "48px",
          maxWidth: "600px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "10px",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontSize: "48px",
              fontWeight: "600",
              color: textColor,
              marginBottom: "12px",
              margin: 0,
            }}
          >
            {isArabic ? "مرحبا بك في" : "Bienvenue sur"}
          </span>
          <span>
            <img
              src={isDark ? "/gold_logo_white.svg" : "/gold_logo_black.svg"}
              alt="logo"
              width={280}
            />
          </span>
        </div>
        <p
          style={{
            fontSize: "16px",
            color: secondaryText,
            margin: 0,
            lineHeight: "1.5",
          }}
        >
          {t.subheading}
        </p>
      </div>
      <div
        style={{
          height: "150px",
        }}
      ></div>
      {/* Features Grid */}
      <div
        style={{
          fontFamily: isArabic ? '"Cairo", sans-serif' : '"Inter", sans-serif',
          display: "flex",
          gap: "24px",
          alignItems: "flex-start",
          flexWrap: "wrap",
          justifyContent: "center",
          marginBottom: "24px",
        }}
      >
        {features.map((feature, idx) => (
          <div
            key={idx}
            style={{
              padding: "24px",
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              gap: "10px",
              width: "300px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                marginBottom: "16px",
                color: secondaryText,
              }}
            >
              {feature.icon}
            </div>
            <h3
              style={{
                fontSize: "16px",
                fontWeight: "500",
                color: secondaryText,
                marginBottom: "16px",
                margin: 0,
              }}
            >
              {feature.title}
            </h3>
            <p
              style={{
                fontSize: "13px",
                fontFamily: isArabic
                  ? '"Cairo", sans-serif'
                  : '"Inter", sans-serif',
                color: secondaryText,
                ontWeight: "300",
                margin: 0,
                lineHeight: "1.5",
              }}
            >
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
