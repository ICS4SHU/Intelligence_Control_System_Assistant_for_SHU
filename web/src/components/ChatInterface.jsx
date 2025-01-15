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
          className="mx-4 my-5 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg flex items-center justify-center gap-2 shadow-lg transition-all duration-300 transform hover:scale-[1.02]"
          onClick={createNewSession}
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">新对话</span>
        </button>

        {/* Navigation Links */}
        <nav className="flex-1">
          <div className="px-3 py-4 space-y-2">
            <a href="#" className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-white/10 rounded-lg transition-colors duration-200">
              <MessageSquare className="w-5 h-5 text-blue-400" />
              <span className="font-medium">解析助手</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-white/10 rounded-lg transition-colors duration-200">
              <History className="w-5 h-5 text-purple-400" />
              <span className="font-medium">考试助手</span>
            </a>
            <button 
              onClick={() => setShowFavorites(!showFavorites)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-gray-300 rounded-lg transition-colors duration-200 ${
                showFavorites ? 'bg-white/15' : 'hover:bg-white/10'
              }`}
            >
              <Bookmark className="w-5 h-5 text-yellow-400" />
              <span className="font-medium">我的收藏</span>
            </button>
          </div>
        </nav>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-3 py-4">
            <h2 className="px-4 py-2 text-sm font-semibold text-gray-400/80 uppercase tracking-wider">
              {showFavorites ? '收藏的对话' : '最近对话'}
            </h2>
            <div className="space-y-1">
              {(showFavorites ? favorites : conversations).map((conv) => (
                <button
                  key={conv.id}
                  className={`w-full text-left px-4 py-3 text-gray-300 rounded-lg transition-all duration-200 ${
                    currentConversationId === conv.id 
                      ? 'bg-white/15 shadow-inner' 
                      : 'hover:bg-white/10'
                  }`}
                  onClick={() => switchSession(conv.id)}
                >
                  <div className="flex items-center gap-3">
                    <MessageSquare className="w-4 h-4 text-gray-400" />
                    <span className="font-medium truncate">{conv.name || '新对话'}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {currentConversation?.messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 relative group ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                    : 'bg-gray-50 shadow-md'
                }`}
              >
                <ReactMarkdown
                  className={`prose ${msg.role === 'user' ? 'prose-invert' : ''} max-w-none`}
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <div className="rounded-lg overflow-hidden my-2">
                          <SyntaxHighlighter
                            language={match[1]}
                            PreTag="div"
                            style={vscDarkPlus}
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        </div>
                      ) : (
                        <code className={`${className} px-1 py-0.5 rounded bg-gray-100`} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
                {msg.role === 'assistant' && msg.id && (
                  <button
                    onClick={() => toggleFavorite(msg.id)}
                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                  >
                    <Star 
                      className={`w-5 h-5 ${
                        currentConversation.user_id === FAVORITE_USER_ID
                          ? 'text-yellow-400 fill-yellow-400'
                          : 'text-gray-400 hover:text-yellow-400'
                      }`}
                    />
                  </button>
                )}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
          {!currentConversation && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
              <MessageSquare className="w-16 h-16" />
              <p className="text-lg font-medium">请先创建或选择一个会话</p>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-100 p-6">
          <div className="flex gap-4 max-w-4xl mx-auto">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息..."
              className="flex-1 p-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none shadow-sm transition-shadow duration-200 hover:shadow-md"
              rows={1}
            />
            <button
              className={`p-4 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl shadow-lg transition-all duration-300 transform hover:scale-[1.02] ${
                isSending ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              onClick={sendMessage}
              disabled={isSending}
            >
              {isSending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
