import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Plus,
  Copy,
  Trash2,
  Loader2,
  Star,
  Search,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import axios from "axios";

// API Configuration
const API_BASE_URL = "http://223.4.250.237";
const API_KEY = "ragflow-E0ZmY5M2E4YmM1MjExZWY4ZWNlMDI0Mm";
const CHAT_ID = "fe9beac2bc2311efb9e60242ac120006";
const AGENT_ID = {
  作业助手: "b76b2488ef6311efb3cf0242ac120006",
  智能助手: "e7074ec2eace11ef8da20242ac120003",
  考试助手: "d8214c5ee7aa11efa80f0242ac120003",
  复习助手: "e3cfde42ed1a11ef9f240242ac120006",
};

// 工具函数
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    alert('已复制到剪贴板');
  });
};

// 会话操作菜单组件
const SessionMenu = ({ session, onRename, onDelete }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        className="p-1 hover:bg-gray-700 rounded"
        onClick={() => setIsOpen(!isOpen)}
      >
        •••
      </button>
      {isOpen && (
        <div className="absolute right-0 mt-2 w-32 bg-gray-800 rounded-lg shadow-lg z-10">
          <button
            className="w-full px-4 py-2 text-left hover:bg-gray-700 rounded-t-lg"
            onClick={onRename}
          >
            重命名
          </button>
          <button
            className="w-full px-4 py-2 text-left hover:bg-gray-700 rounded-b-lg"
            onClick={onDelete}
          >
            删除
          </button>
        </div>
      )}
    </div>
  );
};

const ChatInterface = () => {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('智能助手');
  const [error, setError] = useState(null);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  useEffect(() => {
    loadSessions();
  }, []);

  const userData = JSON.parse(localStorage.getItem("userData"));

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
            orderby: "update_time",
            desc: true,
          },
        }
      );

      if (response.data.code === 0 && Array.isArray(response.data.data)) {
        const sessionsWithMessages = response.data.data.map((session) => ({
          ...session,
          messages: session.messages || [],
        }));
        setConversations(sessionsWithMessages);

        if (sessionsWithMessages.length > 0 && !currentConversationId) {
          switchSession(sessionsWithMessages[0].id);
        }
      }
    } catch (error) {
      setError('会话加载失败');
    } finally {
      setIsLoading(false);
    }
  };

  const switchSession = (sessionId) => {
    if (sessionId === currentConversationId) return;
    const targetSession = conversations.find(
      (conv) => conv.id === sessionId
    );
    if (targetSession) {
      setCurrentConversationId(sessionId);
      setCurrentConversation(targetSession);
    }
  };

  const createNewSession = async () => {
    const sessionName = prompt("请输入会话名称:") || `新会话 ${new Date().toLocaleString()}`;
  
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions`,
        { 
          name: sessionName,
          user_id: userData?.userId,
          agent_id: AGENT_ID[selectedAgent]
        },
        { headers: { Authorization: `Bearer ${API_KEY}` } }
      );

      if (response.data.code === 0) {
        const newSession = {
          ...response.data.data,
          messages: response.data.data.messages || [],
        };
        setConversations((prev) => [newSession, ...prev]);
        switchSession(newSession.id);
      }
    } catch (error) {
      setError('创建会话失败');
    }
  };

  const renameSession = async (sessionId) => {
    const newName = prompt('输入新会话名称:') || `会话 ${new Date().toLocaleDateString()}`;
  
    try {
      await axios.put(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions/${sessionId}`,
        { name: newName },
        { headers: { Authorization: `Bearer ${API_KEY}` } }
      );
      setConversations(prev =>
        prev.map(conv => 
          conv.id === sessionId ? { ...conv, name: newName } : conv
        )
      );
    } catch (error) {
      setError('重命名失败');
    }
  };

  const deleteSession = async (sessionId) => {
    if (!confirm('确定删除该会话？')) return;
  
    try {
      await axios.delete(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/sessions/${sessionId}`,
        { headers: { Authorization: `Bearer ${API_KEY}` } }
      );
      setConversations(prev => prev.filter(conv => conv.id !== sessionId));
      if (currentConversationId === sessionId) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (error) {
      setError('删除会话失败');
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || !currentConversationId || isSending) return;

    setIsSending(true);
    const userMessage = { role: "user", content: inputValue };
    const assistantMessage = { role: "assistant", content: "" };

    const updatedSession = {
      ...currentConversation,
      messages: [
        ...currentConversation.messages,
        userMessage,
        assistantMessage,
      ],
    };
    setCurrentConversation(updatedSession);
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === currentConversationId ? updatedSession : conv
      )
    );
    setInputValue("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chats/${CHAT_ID}/completions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${API_KEY}`,
          },
          body: JSON.stringify({
            question: userMessage.content,
            stream: true,
            session_id: currentConversationId,
            agent_id: AGENT_ID[selectedAgent]
          }),
        }
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data:")) {
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
                      {
                        ...currentConversation.messages.slice(-1)[0],
                        content: assistantResponse,
                        id: data.data.id,
                      },
                    ],
                  };
                  setCurrentConversation(updatedSession);
                  setConversations((prev) =>
                    prev.map((conv) =>
                      conv.id === currentConversationId ? updatedSession : conv
                    )
                  );
                }
              }
            } catch (e) {
              console.error("Error parsing stream data:", e);
            }
          }
        }
      }
    } catch (error) {
      setError('消息发送失败');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const MessageBubble = ({ message }) => {
    const [showActions, setShowActions] = useState(false);

    return (
      <div
        className="relative group"
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        <div className={`px-4 py-2 max-w-[70%] rounded-lg relative ${
          message.role === 'user' 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-200'
        }`}>
          <ReactMarkdown
            components={{
              code: ({ node, inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                if (!inline && match) {
                  return (
                    <div className="relative">
                      <button
                        className="absolute right-2 top-2 p-1 bg-gray-700 rounded hover:bg-gray-600"
                        onClick={() => copyToClipboard(String(children))}
                      >
                        <Copy size={16} />
                      </button>
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    </div>
                  );
                }
                return <code className={className} {...props}>{children}</code>;
              },
              table: ({ children }) => (
                <div className="overflow-x-auto">
                  <table className="border-collapse border border-gray-300">
                    {children}
                  </table>
                </div>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-gray-500 pl-4 italic text-gray-600">
                  {children}
                </blockquote>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      
        {showActions && (
          <div className={`absolute flex gap-2 ${message.role === 'user' ? 'left-0' : 'right-0'} -top-4`}>
            <button
              className="p-1 bg-gray-700 rounded hover:bg-gray-600"
              onClick={() => copyToClipboard(message.content)}
            >
              <Copy size={16} />
            </button>
            <button
              className="p-1 bg-gray-700 rounded hover:bg-gray-600"
              onClick={() => alert('收藏功能待实现')}
            >
              <Star size={16} />
            </button>
            {message.role === 'user' && (
              <button
                className="p-1 bg-red-700 rounded hover:bg-red-600"
                onClick={() => {
                  const newMessages = currentConversation.messages.filter(m => m !== message);
                  setCurrentConversation({...currentConversation, messages: newMessages});
                }}
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-[#f0f2f5]">
      {/* 侧边栏 */}
      <div className="w-72 bg-gradient-to-b from-[#1a1c2e] to-[#2d2f42] text-white flex flex-col shadow-xl">
        <div className="p-4 border-b border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <Search className="text-gray-400" />
            <input
              type="text"
              placeholder="搜索会话..."
              className="w-full p-2 bg-gray-800 rounded"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded flex items-center justify-center"
            onClick={createNewSession}
          >
            <Plus className="mr-2" />
            新建会话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {filteredConversations.map((session) => (
            <div
              key={session.id}
              className={`flex justify-between items-center p-2 hover:bg-gray-800 rounded-lg mb-2 ${
                session.id === currentConversationId ? 'bg-gray-800' : ''
              }`}
            >
              <div 
                className="flex-1 cursor-pointer"
                onClick={() => switchSession(session.id)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm text-blue-400">#{session.id.slice(-4)}</span>
                  <h3 className="text-base font-medium truncate">{session.name}</h3>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {session.messages.length}条消息 • 
                  {new Date(session.update_time).toLocaleDateString()}
                </p>
              </div>
              <SessionMenu
                session={session}
                onRename={() => renameSession(session.id)}
                onDelete={() => deleteSession(session.id)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* 主聊天区域 */}
      <div className="flex flex-col flex-1">
        <div className="px-6 py-4 border-b border-gray-300 flex justify-between items-center bg-white">
          <div className="flex items-center gap-4">
            <select
              className="px-4 py-2 bg-gray-100 rounded border border-gray-300"
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
            >
              {Object.keys(AGENT_ID).map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>
            {currentConversation && (
              <h2 className="text-xl font-semibold">
                {currentConversation.name}
              </h2>
            )}
          </div>
          {error && <div className="text-red-500">{error}</div>}
        </div>

        <div className="flex-1 p-6 overflow-y-auto bg-gray-50">
          <div className="max-w-4xl mx-auto space-y-4">
            {currentConversation?.messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <MessageBubble message={message} />
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </div>

        <div className="p-4 border-t border-gray-300 bg-white">
          <div className="max-w-4xl mx-auto flex gap-4 items-start">
            <div className="relative flex-1">
              <textarea
                className="w-full p-3 bg-gray-100 rounded-lg resize-none border border-gray-300 focus:ring-2 focus:ring-blue-400 pr-16"
                rows="2"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="输入消息..."
              />
              {isSending && (
                <div className="absolute right-4 top-4 text-gray-500 flex items-center gap-2">
                  <Loader2 className="animate-spin" size={18} />
                  <span>思考中...</span>
                </div>
              )}
            </div>
            <button
              className="p-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white disabled:opacity-50 flex items-center"
              onClick={sendMessage}
              disabled={isSending || !inputValue.trim()}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;