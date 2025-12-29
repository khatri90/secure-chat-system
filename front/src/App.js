import React, { useState, useEffect, useContext, createContext, useRef } from 'react';
import { Search, Send, Users, Plus, Settings, LogOut, UserPlus, MessageCircle, Phone, Video, MoreVertical, Smile, Paperclip } from 'lucide-react';

// Context for authentication and chat state
const AuthContext = createContext(null);
const ChatContext = createContext(null);

// API Configuration
const API_URL = 'http://127.0.0.1:8000/api';
const WS_URL = 'ws://127.0.0.1:8000/ws';

// Auth Context Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await fetch(`${API_URL}/auth/profile/`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setToken(null);
          }
        } catch (error) {
          console.error('Auth check failed:', error);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setToken(data.access);
        setUser(data.user);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setToken(data.access);
        setUser(data.user);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error };
      }
    } catch (error) {
      return { success: false, error: { detail: 'Network error' } };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Chat Context Provider
const ChatProvider = ({ children }) => {
  const [chatRooms, setChatRooms] = useState([]);
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [friends, setFriends] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const [typingUsers, setTypingUsers] = useState(new Set());
  const [socket, setSocket] = useState(null);
  const { token, user } = useContext(AuthContext);

  const connectWebSocket = (roomId) => {
    if (socket) socket.close();
    
    const newSocket = new WebSocket(`${WS_URL}/chat/${roomId}/?token=${token}`);
    
    newSocket.onopen = () => {
      console.log('WebSocket connected');
    };
    
    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'chat_message':
          setMessages(prev => [...prev, {
            id: data.message_id,
            content: data.content,
            sender: { id: data.sender_id, username: data.sender_username },
            timestamp: data.timestamp,
            is_read: false
          }]);
          break;
        
        case 'typing_indicator':
          if (data.is_typing) {
            setTypingUsers(prev => new Set([...prev, data.username]));
          } else {
            setTypingUsers(prev => {
              const newSet = new Set(prev);
              newSet.delete(data.username);
              return newSet;
            });
          }
          break;
        
        case 'user_status_update':
          if (data.is_online) {
            setOnlineUsers(prev => new Set([...prev, data.user_id]));
          } else {
            setOnlineUsers(prev => {
              const newSet = new Set(prev);
              newSet.delete(data.user_id);
              return newSet;
            });
          }
          break;
      }
    };
    
    newSocket.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    setSocket(newSocket);
  };

  const sendMessage = (content) => {
    if (socket && content.trim()) {
      socket.send(JSON.stringify({
        type: 'chat_message',
        content: content.trim()
      }));
    }
  };

  const sendTyping = (isTyping) => {
    if (socket) {
      socket.send(JSON.stringify({
        type: 'typing',
        is_typing: isTyping
      }));
    }
  };

  return (
    <ChatContext.Provider value={{
      chatRooms, setChatRooms, activeRoom, setActiveRoom,
      messages, setMessages, friends, setFriends,
      onlineUsers, typingUsers, connectWebSocket,
      sendMessage, sendTyping
    }}>
      {children}
    </ChatContext.Provider>
  );
};

// Login Component
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '', password: '', username: '', password_confirm: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useContext(AuthContext);

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    if (isLogin) {
      const result = await login(formData.email, formData.password);
      if (!result.success) {
        setError(result.error);
      }
    } else {
      if (formData.password !== formData.password_confirm) {
        setError("Passwords don't match");
        setLoading(false);
        return;
      }
      const result = await register(formData);
      if (!result.success) {
        setError(Object.values(result.error).flat().join(', '));
      }
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-800 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 w-full max-w-md border border-white/20 shadow-2xl">
        <div className="text-center mb-8">
          <div className="bg-gradient-to-r from-purple-400 to-blue-400 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="text-white" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">SecureChat</h1>
          <p className="text-white/70">End-to-end encrypted messaging</p>
        </div>

        <div className="space-y-6">
          {!isLogin && (
            <div>
              <input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400 backdrop-blur-sm"
                required
              />
            </div>
          )}
          
          <div>
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400 backdrop-blur-sm"
              required
            />
          </div>
          
          <div>
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSubmit();
                }
              }}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400 backdrop-blur-sm"
              required
            />
          </div>

          {!isLogin && (
            <div>
              <input
                type="password"
                placeholder="Confirm Password"
                value={formData.password_confirm}
                onChange={(e) => setFormData({...formData, password_confirm: e.target.value})}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400 backdrop-blur-sm"
                required
              />
            </div>
          )}

          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-xl p-3 text-red-200 text-sm">
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-white/70 hover:text-white transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
};

// Chat Sidebar Component
const ChatSidebar = () => {
  const { user, logout } = useContext(AuthContext);
  const { chatRooms, friends, activeRoom, setActiveRoom, onlineUsers } = useContext(ChatContext);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFriends, setShowFriends] = useState(false);

  return (
    <div className="w-80 bg-gray-900 border-r border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold">{user?.username?.[0]?.toUpperCase()}</span>
            </div>
            <div>
              <p className="text-white font-medium">{user?.username}</p>
              <p className="text-gray-400 text-sm">Online</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <LogOut size={20} />
          </button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-3 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex border-b border-gray-700">
        <button
          onClick={() => setShowFriends(false)}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            !showFriends ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400 hover:text-white'
          }`}
        >
          Chats
        </button>
        <button
          onClick={() => setShowFriends(true)}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            showFriends ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400 hover:text-white'
          }`}
        >
          Friends
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {!showFriends ? (
          chatRooms.length > 0 ? (
            chatRooms.map((room) => (
              <div
                key={room.id}
                onClick={() => setActiveRoom(room)}
                className={`p-4 border-b border-gray-800 cursor-pointer hover:bg-gray-800 transition-colors ${
                  activeRoom?.id === room.id ? 'bg-gray-800' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold">
                        {room.participants?.find(p => p.id !== user?.id)?.username?.[0]?.toUpperCase()}
                      </span>
                    </div>
                    {onlineUsers.has(room.participants?.find(p => p.id !== user?.id)?.id) && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-gray-900"></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {room.participants?.find(p => p.id !== user?.id)?.username}
                    </p>
                    <p className="text-gray-400 text-sm truncate">
                      {room.last_message?.decrypted_content || 'No messages yet'}
                    </p>
                  </div>
                  {room.unread_count > 0 && (
                    <div className="bg-purple-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {room.unread_count}
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-gray-400">
              <MessageCircle size={48} className="mx-auto mb-2 opacity-50" />
              <p>No conversations yet</p>
              <p className="text-sm">Add friends to start chatting!</p>
            </div>
          )
        ) : (
          friends.length > 0 ? (
            friends.map((friendship) => (
              <div
                key={friendship.id}
                className="p-4 border-b border-gray-800 hover:bg-gray-800 transition-colors cursor-pointer"
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold">
                        {friendship.friend.username[0].toUpperCase()}
                      </span>
                    </div>
                    {onlineUsers.has(friendship.friend.id) && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-gray-900"></div>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium">{friendship.friend.username}</p>
                    <p className="text-gray-400 text-sm">
                      {onlineUsers.has(friendship.friend.id) ? 'Online' : 'Offline'}
                    </p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-gray-400">
              <Users size={48} className="mx-auto mb-2 opacity-50" />
              <p>No friends yet</p>
              <button className="mt-2 text-purple-400 hover:text-purple-300 transition-colors">
                <UserPlus size={16} className="inline mr-1" />
                Add friends
              </button>
            </div>
          )
        )}
      </div>
    </div>
  );
};

// Chat Area Component
const ChatArea = () => {
  const { user } = useContext(AuthContext);
  const { activeRoom, messages, typingUsers, sendMessage, sendTyping } = useContext(ChatContext);
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (messageInput.trim()) {
      sendMessage(messageInput);
      setMessageInput('');
      if (isTyping) {
        sendTyping(false);
        setIsTyping(false);
      }
    }
  };

  const handleTyping = () => {
    if (!isTyping) {
      sendTyping(true);
      setIsTyping(true);
    }
    
    clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      sendTyping(false);
      setIsTyping(false);
    }, 1000);
  };

  if (!activeRoom) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <MessageCircle size={64} className="mx-auto mb-4 text-gray-600" />
          <h3 className="text-xl font-semibold text-white mb-2">Welcome to SecureChat</h3>
          <p className="text-gray-400">Select a conversation or start a new one</p>
        </div>
      </div>
    );
  }

  const otherParticipant = activeRoom.participants?.find(p => p.id !== user?.id);

  return (
    <div className="flex-1 flex flex-col bg-gray-950">
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold">
                {otherParticipant?.username?.[0]?.toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-white font-medium">{otherParticipant?.username}</p>
              <p className="text-gray-400 text-sm">
                {typingUsers.size > 0 ? 'Typing...' : 'Online'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800">
              <Phone size={20} />
            </button>
            <button className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800">
              <Video size={20} />
            </button>
            <button className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800">
              <MoreVertical size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender.id === user?.id ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
              message.sender.id === user?.id
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                : 'bg-gray-800 text-white'
            }`}>
              <p>{message.content}</p>
              <p className={`text-xs mt-1 ${
                message.sender.id === user?.id ? 'text-white/70' : 'text-gray-400'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </p>
            </div>
          </div>
        ))}
        
        {typingUsers.size > 0 && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-300 px-4 py-2 rounded-2xl">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-700 bg-gray-900">
        <div className="flex items-center space-x-3">
          <button
            type="button"
            className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
          >
            <Paperclip size={20} />
          </button>
          
          <div className="flex-1 relative">
            <input
              type="text"
              value={messageInput}
              onChange={(e) => {
                setMessageInput(e.target.value);
                handleTyping();
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSendMessage();
                }
              }}
              placeholder="Type a message..."
              className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 pr-12"
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            >
              <Smile size={20} />
            </button>
          </div>
          
          <button
            type="button"
            onClick={handleSendMessage}
            disabled={!messageInput.trim()}
            className="p-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Chat Application
const ChatApp = () => {
  const { user, loading } = useContext(AuthContext);
  const { connectWebSocket, setActiveRoom, setChatRooms, setFriends } = useContext(ChatContext);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    if (user && token) {
      // Fetch chat rooms
      fetch(`${API_URL}/chat/rooms/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => setChatRooms(data))
      .catch(console.error);

      // Fetch friends
      fetch(`${API_URL}/auth/friends/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => setFriends(data))
      .catch(console.error);
    }
  }, [user, token]);

  useEffect(() => {
    // Connect to WebSocket when active room changes
    if (user && token && connectWebSocket) {
      // For demo, we'll connect to room 1 if it exists
      // In real app, connect when user selects a room
    }
  }, [user, token, connectWebSocket]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  return (
    <div className="h-screen flex bg-gray-950">
      <ChatSidebar />
      <ChatArea />
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <AuthProvider>
      <ChatProvider>
        <ChatApp />
      </ChatProvider>
    </AuthProvider>
  );
};

export default App;