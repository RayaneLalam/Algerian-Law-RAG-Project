import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { LanguageThemeProvider } from "./contexts/LanguageThemeContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <LanguageThemeProvider>
      <App />
    </LanguageThemeProvider>
  </React.StrictMode>
);
