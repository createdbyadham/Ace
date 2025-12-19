import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, X, Maximize2, Minimize2, Send, Trash2, Sparkles, Bot } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { chatbotApi } from './api';
import type { ChatMessage } from './types';

type ViewMode = 'closed' | 'window' | 'fullscreen';

export function ChatBot() {
  const [viewMode, setViewMode] = useState<ViewMode>('closed');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (viewMode !== 'closed' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [viewMode]);

  // Handle escape key to close fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && viewMode === 'fullscreen') {
        setViewMode('window');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [viewMode]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await chatbotApi.chat({
        message: userMessage.content,
        session_id: sessionId ?? undefined,
      });

      if (!sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (sessionId) {
      try {
        await chatbotApi.clearSession(sessionId);
      } catch {
        // Session might not exist on server, that's okay
      }
    }
    setMessages([]);
    setSessionId(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleViewMode = () => {
    setViewMode((current) => {
      if (current === 'closed') return 'window';
      if (current === 'window') return 'closed';
      return 'window';
    });
  };

  const toggleFullscreen = () => {
    setViewMode((current) => (current === 'fullscreen' ? 'window' : 'fullscreen'));
  };

  // Floating button when closed
  if (viewMode === 'closed') {
    return (
      <button
        onClick={toggleViewMode}
        className="fixed bottom-6 right-6 z-50 group"
        aria-label="Open chat"
      >
        <div className="relative">
          {/* Glow effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full blur-lg opacity-50 group-hover:opacity-75 transition-opacity duration-300" />
          
          {/* Main button */}
          <div className="relative flex items-center justify-center w-14 h-14 bg-black hover:bg-black/80 text-white outline outline-2 outline-white/10 rounded-full shadow-[0_0_20px_4px_rgba(99,102,241,0.25)] transform transition-all duration-300 group-hover:scale-110">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          
          {/* Pulse animation */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 animate-ping opacity-20" />
        </div>
      </button>
    );
  }

  const isFullscreen = viewMode === 'fullscreen';

  return (
    <>
      {/* Backdrop for fullscreen */}
      {isFullscreen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" 
          onClick={() => setViewMode('window')}
        />
      )}

      {/* Chat container */}
      <div
        className={cn(
          'fixed z-50 flex flex-col bg-background/95 backdrop-blur-xl border border-white/10 shadow-2xl transition-all duration-300 ease-out',
          isFullscreen
            ? 'inset-4 md:inset-8 lg:inset-16 rounded-2xl animate-in zoom-in-95 duration-200'
            : 'bottom-6 right-6 w-[380px] h-[520px] rounded-2xl animate-in slide-in-from-bottom-4 duration-300'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 bg-black text-white outline outline-2 outline-white/10 rounded-xl shadow-lg">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-foreground">Cardify AI</h3>
              <p className="text-xs text-muted-foreground">Powered by RAG</p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClearChat}
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                title="Clear chat"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleFullscreen}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleViewMode}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              title="Close chat"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4 animate-in fade-in duration-500">
              <div className="relative">
                <div className="absolute inset-0 bg-black rounded-full blur-xl opacity-30" />
                <div className="relative flex items-center justify-center w-16 h-16 bg-black text-white outline outline-2 outline-white/10 rounded-full border border-white/10">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
              </div>
              <div>
                <h4 className="font-semibold text-foreground mb-1">How can I help you?</h4>
                <p className="text-sm text-muted-foreground max-w-[260px]">
                  Ask me anything about your uploaded documents. I'll find the answers for you.
                </p>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={message.id}
                className={cn(
                  'flex animate-in slide-in-from-bottom-2 duration-300',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div
                  className={cn(
                    'max-w-[85%] px-4 py-2.5 rounded-2xl',
                    message.role === 'user'
                      ? 'bg-black text-white rounded-br-md'
                      : 'bg-secondary/80 text-foreground rounded-bl-md border border-white/5'
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  
                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-white/10">
                      <p className="text-xs text-muted-foreground mb-1">Sources:</p>
                      <div className="flex flex-wrap gap-1">
                        {message.sources.map((source, idx) => (
                          <span
                            key={idx}
                            className="text-xs px-2 py-0.5 bg-white/10 rounded-full text-muted-foreground"
                          >
                            {source}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start animate-in fade-in duration-200">
              <div className="bg-secondary/80 px-4 py-3 rounded-2xl rounded-bl-md border border-white/5">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-white/10 bg-background/50">
          <div className="flex items-center gap-2 bg-secondary/50 rounded-xl px-4 py-2 border border-white/5 focus-within:border-indigo-500/50 transition-colors">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message..."
              disabled={isLoading}
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              size="icon"
              className="h-8 w-8 bg-black hover:bg-black/80 text-white rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-2">
            Press Enter to send • Esc to minimize
          </p>
        </div>
      </div>
    </>
  );
}

