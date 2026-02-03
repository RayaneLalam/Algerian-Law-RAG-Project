import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useLanguageTheme } from '../contexts/LanguageThemeContext';

export const Login = ({ onSwitchToRegister }) => {
  const { login } = useAuth();
  const { language, theme } = useLanguageTheme();
  const isArabic = language === 'ar';
  const isDark = theme === 'dark';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  const bgColor = isDark ? '#2a2a2a' : '#ffffff';
  const textColor = isDark ? '#ffffff' : '#000000';
  const inputBg = isDark ? '#3a3a3a' : '#f5f5f5';
  const borderColor = isDark ? '#4a4a4a' : '#ddd';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: isDark ? '#232323' : '#f1f1f1',
        padding: '20px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          backgroundColor: bgColor,
          borderRadius: '12px',
          padding: '40px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}
      >
        <h2
          style={{
            color: textColor,
            textAlign: 'center',
            marginBottom: '30px',
            fontSize: '24px',
          }}
        >
          {isArabic ? 'تسجيل الدخول' : 'Login'}
        </h2>

        {error && (
          <div
            style={{
              backgroundColor: '#fee',
              color: '#c33',
              padding: '12px',
              borderRadius: '6px',
              marginBottom: '20px',
              fontSize: '14px',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                color: textColor,
                marginBottom: '8px',
                fontSize: '14px',
              }}
            >
              {isArabic ? 'اسم المستخدم' : 'Username'}
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: inputBg,
                color: textColor,
                border: `1px solid ${borderColor}`,
                borderRadius: '6px',
                fontSize: '14px',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label
              style={{
                display: 'block',
                color: textColor,
                marginBottom: '8px',
                fontSize: '14px',
              }}
            >
              {isArabic ? 'كلمة المرور' : 'Password'}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: inputBg,
                color: textColor,
                border: `1px solid ${borderColor}`,
                borderRadius: '6px',
                fontSize: '14px',
                outline: 'none',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isLoading ? '#999' : '#007bff',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s',
            }}
          >
            {isLoading
              ? (isArabic ? 'جاري تسجيل الدخول...' : 'Logging in...')
              : (isArabic ? 'تسجيل الدخول' : 'Login')}
          </button>
        </form>

        <div
          style={{
            marginTop: '20px',
            textAlign: 'center',
            color: textColor,
            fontSize: '14px',
          }}
        >
          {isArabic ? 'ليس لديك حساب؟' : "Don't have an account?"}{' '}
          <button
            onClick={onSwitchToRegister}
            style={{
              background: 'none',
              border: 'none',
              color: '#007bff',
              textDecoration: 'underline',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            {isArabic ? 'سجل الآن' : 'Register'}
          </button>
        </div>
      </div>
    </div>
  );
};