import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // 使用 useNavigate 替代 useHistory
import axios from 'axios';

const ChatInterface = () => {
  const navigate = useNavigate(); // 使用 useNavigate
  const [conversations, setConversations] = useState([]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [userToken, setUserToken] = useState(localStorage.getItem('userToken')); // 从localStorage获取用户的token

  // 检查用户是否已登录
  useEffect(() => {
    if (!userToken) {
      navigate('/login'); // 未登录用户跳转到登录页面
    }
  }, [userToken, navigate]);

  // 获取历史对话记录
  const fetchConversations = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('http://223.4.250.237/api/v1/chat/conversations', {
        headers: {
          Authorization: `Bearer ${userToken}`,
        },
      });
      if (response.data.code === 0) {
        setConversations(response.data.data);
      } else {
        setError('无法加载对话记录');
      }
    } catch (error) {
      setError('获取对话记录失败');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (userToken) {
      fetchConversations(); // 只有在用户登录时才会请求对话记录
    }
  }, [userToken]);

  // 处理发送消息
  const handleSendMessage = async () => {
    if (!message.trim()) return; // 防止发送空消息

    try {
      const response = await axios.post(
        'http://223.4.250.237/api/v1/chat/message',
        { message },
        {
          headers: {
            Authorization: `Bearer ${userToken}`,
          },
        }
      );
      if (response.data.code === 0) {
        setMessage('');
        fetchConversations(); // 重新获取对话记录
      } else {
        setError('发送消息失败');
      }
    } catch (error) {
      setError('发送消息请求失败');
      console.error(error);
    }
  };

  // 处理注销登录
  const handleLogout = () => {
    localStorage.removeItem('userToken'); // 清除本地存储的 token
    setUserToken(null); // 更新状态
    navigate('/login'); // 跳转回登录页面
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-blue-500 text-white p-4 flex justify-between items-center">
        <h1 className="text-xl">聊天界面</h1>
        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-600 py-2 px-4 rounded-lg"
        >
          注销
        </button>
      </header>

      <main className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div>加载中...</div>
        ) : error ? (
          <div className="text-red-500">{error}</div>
        ) : (
          <div>
            {conversations.length === 0 ? (
              <div>没有聊天记录</div>
            ) : (
              conversations.map((conversation, index) => (
                <div key={index} className="mb-4">
                  <div className="text-gray-600">{conversation.user}</div>
                  <div>{conversation.message}</div>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      <footer className="bg-white p-4 border-t border-gray-300">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="请输入消息..."
          className="w-full p-2 border border-gray-300 rounded-lg"
        />
        <button
          onClick={handleSendMessage}
          className="mt-2 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
        >
          发送
        </button>
      </footer>
    </div>
  );
};

export default ChatInterface;
