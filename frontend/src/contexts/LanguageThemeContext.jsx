import React, { createContext, useState, useCallback } from "react";

export const LanguageThemeContext = createContext();

export const LanguageThemeProvider = ({ children }) => {
  const [language, setLanguage] = useState("fr"); // 'fr' or 'ar'
  const [theme, setTheme] = useState("light"); // 'dark' or 'light'

  const toggleLanguage = useCallback(() => {
    setLanguage((prev) => (prev === "fr" ? "ar" : "fr"));
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const t = {
    fr: {
      newChat: "Nouvelle conversation",
      recent: "RÉCENT",
      messageAI: "Message Konan.ai...",
      howCanIHelp: "Comment puis-je vous aider?",
      welcome: "Bienvenue sur Konan.ai",
      subheading:
        "Votre assistant intelligent pour comprendre le droit algérien.",
      example:
        'Exemple : "Résumé l\'Article 15 du Code de la Famille en termes simples"',
      reliableSources: "Sources juridiques fiables",
      reliableSourcesDesc:
        "Toutes les réponses proviennent de textes officiels publiés dans les journaux et portails gouvernementaux algériens.",
      bilingualExplanations: "Explications bilingues",
      bilingualExplanationsDesc:
        "Comprenez le droit en arabe et en français, instantanément et sans complexité.",
      intelligentAnalysis: "Analyse juridique intelligente",
      intelligentAnalysisDesc:
        "Recherchez, résumez et explorez les lois grâce à la puissance de l'intelligence artificielle.",
      disclaimer:
        "Konan.ai peut faire des erreurs. Veuillez vérifier les informations importantes.",
      language: "Langue",
      theme: "Mode",
      lightMode: "Mode clair",
      darkMode: "Mode sombre",
      updates: "Mises à jour & FAQ",
      logout: "Se déconnecter",
    },
    ar: {
      newChat: " محادثة جديدة",
      recent: "الأخيرة",
      messageAI: "رسالة Konan.ai...",
      howCanIHelp: "كيف يمكنني مساعدتك؟",
      welcome: "مرحبا بك في Konan.ai",
      subheading: "مساعدك الذكي لفهم القانون الجزائري.",
      example: 'مثال: "ملخص المادة 15 من قانون الأسرة بطريقة مبسطة"',
      reliableSources: "مصادر قانونية موثوقة",
      reliableSourcesDesc:
        "جميع الإجابات مستخرجة من النصوص الرسمية المنشورة في الجرائد والمواقع الحكومية الجزائرية.",
      bilingualExplanations: "شروحات ثنائية اللغة",
      bilingualExplanationsDesc:
        "افهم القانون بالعربية والفرنسية، فوراً وبكل وضوح.",
      intelligentAnalysis: "تحليل قانوني ذكي",
      intelligentAnalysisDesc:
        "ابحث، لخص واستكشف القوانين باستخدام قوة الذكاء الاصطناعي.",
      disclaimer: "Konan.ai يمكن أن يخطئ. يرجى التحقق من المعلومات المهمة.",
      language: "اللغة",
      theme: "المظهر",
      lightMode: "وضع مضاء",
      darkMode: "وضع مظلم",
      updates: "تحديثات والأسئلة الشائعة",
      logout: "تسجيل الخروج",
    },
  };

  return (
    <LanguageThemeContext.Provider
      value={{
        language,
        theme,
        toggleLanguage,
        toggleTheme,
        t: t[language],
      }}
    >
      {children}
    </LanguageThemeContext.Provider>
  );
};

export const useLanguageTheme = () => {
  const context = React.useContext(LanguageThemeContext);
  if (!context) {
    throw new Error(
      "useLanguageTheme must be used within LanguageThemeProvider"
    );
  }
  return context;
};
