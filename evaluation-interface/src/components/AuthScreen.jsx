// components/AuthScreen.jsx
import React from 'react';
import Login from './Login';

const AuthScreen = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl flex items-center justify-center gap-12">
        {/* Left side - Branding */}
        <div className="hidden lg:block flex-1 text-center">
          <div className="mb-8">
            <h1 className="text-5xl font-bold text-gray-800 mb-4">Evaluator UI</h1>
            <p className="text-xl text-gray-600">
              Advanced AI Model Evaluation Platform
            </p>
          </div>
          <div className="space-y-4 text-left max-w-md mx-auto">
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                ✓
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">RLHF Evaluation</h3>
                <p className="text-gray-600 text-sm">Rank and evaluate model responses with human feedback</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                ✓
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Performance Metrics</h3>
                <p className="text-gray-600 text-sm">Track and compare model performance across datasets</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                ✓
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Query Review</h3>
                <p className="text-gray-600 text-sm">Identify and flag hallucinations in model responses</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right side - Login */}
        <div className="flex-1 flex items-center justify-center">
          <Login />
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;