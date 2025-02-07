import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../css/LoginPage.css'; // 导入CSS文件

const LoginPage = ({ onLogin }) => {
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    if (!loginId || !password) {
      setError("用户名/学号和密码不能为空");
      return;
    }

    try {
      const response = await axios.post('/login', { login_id: loginId, password });
      if (response.data.access_token) {
        onLogin(response.data.access_token); // 传递token到父组件
        navigate('/chat'); // 登录成功后跳转到聊天页面
      } else {
        setError('登录失败，请检查用户名/学号或密码');
      }
    } catch (error) {
      setError('登录失败，请稍后再试');
      console.error('登录失败', error);
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>Login</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Username/Student ID:</label>
            <input
              type="text"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="login-button">Login</button>
        </form>

        <button onClick={() => navigate('/register')} className="register-button">
          Go to Register
        </button>
      </div>
    </div>
  );
};

export default LoginPage;
