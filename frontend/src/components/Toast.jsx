import React, { useState, useEffect } from 'react';

export const Toast = ({ message, type = 'info', duration = 3000, onClose }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      onClose && onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!visible) return null;

  const typeStyles = {
    info: 'bg-blue-500 text-white',
    success: 'bg-green-500 text-white', 
    warning: 'bg-yellow-500 text-black',
    error: 'bg-red-500 text-white'
  };

  return (
    <div className={`fixed top-4 right-4 p-3 rounded-lg shadow-lg z-50 max-w-sm ${typeStyles[type]}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm">{message}</span>
        <button 
          onClick={() => {
            setVisible(false);
            onClose && onClose();
          }}
          className="ml-2 text-lg font-bold hover:opacity-75"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export const useToast = () => {
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = 'info', duration = 3000) => {
    const id = Date.now();
    const toast = { id, message, type, duration };
    
    setToasts(prev => [...prev, toast]);
    
    // Auto-remove toast after duration
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration + 100);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const ToastContainer = () => (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );

  return { showToast, ToastContainer };
};