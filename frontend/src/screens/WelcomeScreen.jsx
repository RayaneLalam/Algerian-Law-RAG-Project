import React, { useState, useEffect } from "react";
import { useLanguageTheme } from "../contexts/LanguageThemeContext";
import { MdOutlineBalance, MdLanguage, MdSmartToy } from "react-icons/md";

export const WelcomeScreen = () => {
  const { language, theme, t } = useLanguageTheme();
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  
  const isArabic = language === "ar";
  const isDark = theme === "dark";
  const isSmallScreen = windowWidth < 900;

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const textColor = isDark ? "#ffffff" : "#1c1c1c";
  const secondaryText = isDark ? "#adadad" : "#6b6b6b";

  const features = [
    { icon: <MdOutlineBalance size={isSmallScreen ? 22 : 28} />, title: t.reliableSources, desc: t.reliableSourcesDesc },
    { icon: <MdLanguage size={isSmallScreen ? 22 : 28} />, title: t.bilingualExplanations, desc: t.bilingualExplanationsDesc },
    { icon: <MdSmartToy size={isSmallScreen ? 22 : 28} />, title: t.intelligentAnalysis, desc: t.intelligentAnalysisDesc },
  ];

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: isDark
          ? "radial-gradient(ellipse at center bottom, rgba(212,175,55,0.12) 0%, #232323 70%)"
          : "radial-gradient(ellipse at center bottom, rgba(212,175,55,0.18) 0%, #f1f1f1 70%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: isSmallScreen ? "15px" : "40px 24px",
        boxSizing: "border-box",
        overflow: "hidden",
        position: "relative"
      }}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* 1. Header Section */}
      <div style={{ 
        textAlign: "center", 
        marginTop: isSmallScreen ? "5px" : "40px", // Pushed down slightly more from top
        zIndex: 2 
      }}>
        <div style={{ 
          display: "flex", 
          gap: "12px", 
          justifyContent: "center", 
          alignItems: "center" 
        }}>
          <span style={{ 
            fontSize: isSmallScreen ? "22px" : "40px", 
            fontWeight: "600", 
            color: textColor 
          }}>
            {isArabic ? "مرحبا بك في" : "Bienvenue sur"}
          </span>
          <img
            src={isDark ? "/gold_logo_white.svg" : "/gold_logo_black.svg"}
            alt="logo"
            style={{ width: isSmallScreen ? "150px" : "240px" }}
          />
        </div>
        <p style={{ 
          fontSize: isSmallScreen ? "13px" : "17px", 
          color: secondaryText, 
          marginTop: "8px",
          maxWidth: "550px" 
        }}>
          {t.subheading}
        </p>
      </div>

      {/* 2. Flexible Spacer - pushes content apart */}
      <div style={{ flex: 1 }} />

      {/* 3. Features Section */}
      <div
        style={{
          display: "flex",
          gap: isSmallScreen ? "10px" : "24px",
          flexDirection: isSmallScreen ? "column" : "row",
          width: "100%",
          maxWidth: "1100px",
          justifyContent: "center",
          alignItems: "stretch", 
          
          /* INCREASED MARGIN: This is the distance from the InputArea */
          marginBottom: isSmallScreen ? "110px" : "50px", 
          
          zIndex: 2,
          padding: isSmallScreen ? "0 10px" : "0 40px",
          transition: "margin-bottom 0.3s ease"
        }}
      >
        {features.map((f, i) => (
          <div
            key={i}
            style={{
              padding: isSmallScreen ? "12px 15px" : "24px",
              textAlign: isSmallScreen ? (isArabic ? "right" : "left") : "center",
              display: "flex",
              flexDirection: isSmallScreen ? "row" : "column",
              alignItems: "center",
              gap: isSmallScreen ? "15px" : "16px",
              flex: isSmallScreen ? "none" : 1,
              width: isSmallScreen ? "100%" : "auto",
              
              backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.7)",
              borderRadius: "18px",
              border: `1px solid ${isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)"}`,
              boxSizing: "border-box",
              boxShadow: isDark ? "none" : "0 4px 12px rgba(0,0,0,0.03)"
            }}
          >
            <div style={{ color: secondaryText, display: "flex", flexShrink: 0 }}>
              {f.icon}
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ 
                fontSize: isSmallScreen ? "14px" : "16px", 
                fontWeight: "600", 
                color: textColor, 
                margin: 0,
                marginBottom: isSmallScreen ? "0" : "10px"
              }}>
                {f.title}
              </h3>
              {!isSmallScreen && (
                <p style={{ 
                  fontSize: "13px", 
                  color: secondaryText, 
                  lineHeight: "1.6",
                  margin: 0 
                }}>
                  {f.desc}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 4. Invisible Bottom Padding - Visual safeguard */}
      <div style={{ 
        height: isSmallScreen ? "20px" : "40px", 
        width: "100%", 
        flexShrink: 0 
      }} />
    </div>
  );
};