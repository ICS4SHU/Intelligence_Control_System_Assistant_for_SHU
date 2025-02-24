import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../css/RegisterPage.css';

const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [studentId, setStudentId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const apiBaseUrl = 'http://127.0.0.1:8000'; // 直接在代码中设置 base URL

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${apiBaseUrl}/api/v1/auth/register`, {
        username,
        studentId,
        email,
        password,
      });

      // 注册成功后端返回 200，直接跳转到登录页面
    navigate('/login');
  } catch (error) {
    // 处理错误响应
    if (error.response) {
      // 后端返回了错误信息，如 400 等
      setError(error.response.data.detail || '注册失败');
    } else {
      setError('注册失败，请检查网络或联系管理员');
    }
    console.error('注册失败', error);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="register-container">
      <div className="register-form">
        <h2>Register</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label>Username:</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Student ID:</label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
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
          <button type="submit" className="register-button" disabled={loading}>
            {loading ? '注册中...' : 'Register'}
          </button>
        </form>

        <button onClick={() => navigate('/login')} className="login-button">
          Go to Login
        </button>
      </div>
    </div>
  );
};

export default RegisterPage;
