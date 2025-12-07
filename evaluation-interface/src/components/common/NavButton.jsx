import React from 'react';

const NavButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
      active ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
    }`}
  >
    {children}
  </button>
);

export default NavButton;