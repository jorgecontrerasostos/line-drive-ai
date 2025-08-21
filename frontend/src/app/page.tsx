"use client"

import { Send } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm LineDrive AI, an AI assistant created to answer questions about MLB players. How can I help you today?",
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async() => {
    if (inputValue.trim() === '' || isLoading) return;

    const newUserMessage = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/chat?question=${encodeURIComponent(inputValue)}`, {
      method: 'POST'})
        
      const data = await response.json();
      const assistantResponse = {
        id: Date.now(),
        text: data.answer,
        sender: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantResponse]);

    } catch (error) {
      console.error('Error calling API:', error);
      const errorResponse = {
        id: Date.now(),
        text: 'Sorry, I encountered an error. Please try again later.',
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: { key: string; shiftKey: any; preventDefault: () => void; }) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="flex flex-col h-screen max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="border-b border-gray-100 p-4 bg-white sticky top-0 z-10">
        <h1 className="text-xl font-semibold text-gray-800">LineDrive AI</h1>
        <p className="text-sm text-gray-500 mt-1">Your MLB analytics assistant</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`w-full ${
              message.sender === 'user' ? 'bg-transparent' : 'bg-white border-t border-gray-100'
            }`}
          >
            <div className="max-w-3xl mx-auto px-4 py-6">
              <div className={`flex items-start space-x-4 ${
                message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                  message.sender === 'user' ? 'bg-blue-500' : 'bg-gray-700'
                }`}>
                  {message.sender === 'user' ? 'You' : 'AI'}
                </div>
                
                {/* Message Content */}
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium mb-1 ${
                    message.sender === 'user' ? 'text-right text-gray-700' : 'text-gray-700'
                  }`}>
                    {message.sender === 'user' ? 'You' : 'LineDrive AI'}
                  </div>
                  <div className={`prose max-w-none ${
                    message.sender === 'user' ? 'text-right' : ''
                  }`}>
                    <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{message.text}</p>
                  </div>
                  <p className={`text-xs mt-2 text-gray-400 ${
                    message.sender === 'user' ? 'text-right' : ''
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {/* Loading Spinner */}
        {isLoading && (
          <div className="w-full bg-white border-t border-gray-100">
            <div className="max-w-3xl mx-auto px-4 py-6">
              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white text-sm font-medium">
                  AI
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium mb-1 text-gray-700">LineDrive AI</div>
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-75"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></div>
                    </div>
                    <span className="text-sm text-gray-500">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-100 bg-white p-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about any MLB player..."
                rows={1}
                className="w-full resize-none border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400 text-sm leading-relaxed min-h-[44px] max-h-32 overflow-y-auto text-gray-800 shadow-sm"
                style={{ scrollbarWidth: 'thin' }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={inputValue.trim() === '' || isLoading}
              className="flex items-center justify-center w-10 h-10 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex-shrink-0 shadow-sm"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <Send size={16} />
              )}
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-400 text-center">
            Press Enter to send, Shift + Enter for new line
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}