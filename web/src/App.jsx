import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';

function App() {
  const [userToken, setUserToken] = useState(localStorage.getItem('userToken')); // 从 localStorage 获取用户 token

  const handleLogin = (token) => {
    setUserToken(token);
    localStorage.setItem('userToken', token); // 保存 token 到 localStorage
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/chat"
          element={userToken ? <ChatInterface /> : <LoginPage onLogin={handleLogin} />}
        />
        <Route path="/" element={<LoginPage onLogin={handleLogin} />} />
      </Routes>
    </Router>
  );
}

export default App;
