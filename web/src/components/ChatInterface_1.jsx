import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, MessageSquare, History, Bookmark, Copy, Trash2, Loader2, Star } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import axios from 'axios';

// API Configuration
const API_BASE_URL = 'http://223.4.250.237';
const API_KEY = 'ragflow-E0ZmY5M2E4YmM1MjExZWY4ZWNlMDI0Mm';
const CHAT_ID = 'fe9beac2bc2311efb9e60242ac120006';
const FAVORITE_USER_ID = 'favorite_user';

const ChatInterface = () => {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [showFavorites, setShowFavorites] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const chatEndRef = useRef(null);


  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  useEffect(() => {
    loadSessions();
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions`,
        {
          headers: { Authorization: `Bearer ${API_KEY}` },
          params: {
            page: 1,
            page_size: 30,
            user_id: FAVORITE_USER_ID
          }
        }
      );

      if (response.data.code === 0 && Array.isArray(response.data.data)) {
        setFavorites(response.data.data);
      }
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions`,
        {
          headers: { Authorization: `Bearer ${API_KEY}` },
          params: {
            page: 1,
            page_size: 30,
            orderby: 'update_time',
            desc: true
          }
        }
      );

      if (response.data.code === 0 && Array.isArray(response.data.data)) {
        const sessionsWithMessages = response.data.data.map(session => ({
          id: session.id,
          name: session.name,
          messages: session.messages || [],
          user_id: session.user_id
        }));
        setConversations(sessionsWithMessages);

        if (sessionsWithMessages.length > 0 && !currentConversationId) {
          switchSession(sessionsWithMessages[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleFavorite = async (messageId) => {
    const session = conversations.find(conv =>
      conv.messages.some(msg => msg.id === messageId)
    );

    if (!session) return;

    const isFavorite = session.user_id === FAVORITE_USER_ID;

    try {
      await axios.put(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions/${session.id}`,
        {
          name: session.name,
          user_id: isFavorite ? '' : FAVORITE_USER_ID
        },
        { headers: { Authorization: `Bearer ${API_KEY}` } }
      );

      const updatedConversations = conversations.map(conv =>
        conv.id === session.id
          ? { ...conv, user_id: isFavorite ? '' : FAVORITE_USER_ID }
          : conv
      );
      setConversations(updatedConversations);
      loadFavorites();
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const switchSession = (sessionId) => {
    if (sessionId === currentConversationId) return;
    const targetSession = [...conversations, ...favorites].find(conv => conv.id === sessionId);
    if (targetSession) {
      setCurrentConversationId(sessionId);
      setCurrentConversation(targetSession);
    }
  };

  const createNewSession = async () => {
    const sessionName = prompt('请输入会话名称:');
    if (!sessionName) return;

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions`,
        { name: sessionName },
        { headers: { Authorization: `Bearer ${API_KEY}` } }
      );

      if (response.data.code === 0) {
        const newSession = {
          id: response.data.data.id,
          name: sessionName,
          messages: response.data.data.messages || [],
          user_id: ''
        };
        setConversations(prev => [newSession, ...prev]);
        switchSession(newSession.id);
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || !currentConversationId || isSending) return;

    setIsSending(true);
    const userMessage = { role: 'user', content: inputValue };
    const assistantMessage = { role: 'assistant', content: '' };

    const updatedSession = {
      ...currentConversation,
      messages: [...currentConversation.messages, userMessage, assistantMessage]
    };
    setCurrentConversation(updatedSession);
    setConversations(prev =>
      prev.map(conv =>
        conv.id === currentConversationId ? updatedSession : conv
      )
    );
    setInputValue('');

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/completions`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${API_KEY}`
          },
          body: JSON.stringify({
            question: userMessage.content,
            stream: true,
            session_id: currentConversationId
          })
        }
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5));
              if (data.code === 0) {
                if (data.data === true) {
                  break;
                } else if (data.data.answer) {
                  assistantResponse = data.data.answer;
                  const updatedSession = {
                    ...currentConversation,
                    messages: [
                      ...currentConversation.messages.slice(0, -1),
                      { role: 'assistant', content: assistantResponse, id: data.data.id }
                    ]
                  };
                  setCurrentConversation(updatedSession);
                  setConversations(prev =>
                    prev.map(conv =>
                      conv.id === currentConversationId ? updatedSession : conv
                    )
                  );
                }
              }
            } catch (e) {
              console.error('Error parsing stream data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-[#f0f2f5]">
      {/* Sidebar */}
      <div className="w-72 bg-gradient-to-b from-[#1a1c2e] to-[#2d2f42] text-white flex flex-col shadow-xl">
        {/* Header */}
        <div className="p-6 border-b border-gray-700/50">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Learning Assistant
          </h1>
        </div>

        {/* New Chat Button */}
        <button
          className="mx-4 my-5 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg flex items-center justify-center"
          onClick={createNewSession}
        >
          <Plus className="mr-2" />
          新建会话
        </button>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          <div className="mx-4 my-3">
            {showFavorites ? (
              <>
                <button className="w-full text-left text-lg mb-2" onClick={() => setShowFavorites(false)}>
                  所有会话
                </button>
                <ul className="space-y-2">
                  {favorites.map((session) => (
                    <li
                      key={session.id}
                      className="cursor-pointer hover:bg-gray-800 p-2 rounded-lg"
                      onClick={() => switchSession(session.id)}
                    >
                      <h3 className="text-lg font-medium">{session.name}</h3>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <>
                <button className="w-full text-left text-lg mb-2" onClick={() => setShowFavorites(true)}>
                  收藏会话
                </button>
                <ul className="space-y-2">
                  {conversations.map((session) => (
                    <li
                      key={session.id}
                      className="cursor-pointer hover:bg-gray-800 p-2 rounded-lg"
                      onClick={() => switchSession(session.id)}
                    >
                      <h3 className="text-lg font-medium">{session.name}</h3>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Chat Content */}
      <div className="flex flex-col w-full">
        {/* Chat Header */}
        <div className="px-5 py-4 border-b border-gray-300 flex justify-between items-center">
          {currentConversation ? (
            <h2 className="text-2xl font-semibold">{currentConversation.name}</h2>
          ) : (
            <h2 className="text-2xl font-semibold">请选择会话</h2>
          )}
        </div>

        {/* Chat Messages */}
        <div className="flex-1 p-5 overflow-y-auto">
          <div className="space-y-4">
            {currentConversation?.messages.map((message, idx) => (
              <div key={idx} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`px-4 py-2 max-w-[70%] rounded-lg ${
                    message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200'
                  }`}
                >
                  <ReactMarkdown
                    components={{
                      code: ({ node, inline, className, children, ...props }) => {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" {...props}>
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
          <div ref={chatEndRef}></div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-300 p-4 flex items-center space-x-4">
          <textarea
            className="w-full p-3 bg-gray-200 rounded-lg resize-none"
            rows="2"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="输入消息..."
          />
          <button
            className="p-3 bg-blue-500 rounded-lg text-white"
            onClick={sendMessage}
            disabled={isSending || !inputValue.trim()}
          >
            {isSending ? <Loader2 className="animate-spin" /> : <Send />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
