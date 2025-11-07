'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { AppShell } from '@/components/layout/app-shell';
import { chatApi } from '@/lib/api/chat';
import type { ChatSession, ChatMessage, Citation } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, Send, Plus, Trash2, FileText } from 'lucide-react';
import { ProtectedRoute } from '@/components/protected-route';

function ChatPage() {
  const { user, getToken } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load messages when session changes
  useEffect(() => {
    if (currentSession) {
      loadMessages(currentSession.id);
    }
  }, [currentSession]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const loadSessions = async () => {
    try {
      const data = await chatApi.listSessions();
      setSessions(data.sessions);

      // If no current session and there are sessions, select the first one
      if (!currentSession && data.sessions.length > 0) {
        setCurrentSession(data.sessions[0]);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      toast.error('Failed to load chat sessions');
    }
  };

  const loadMessages = async (sessionId: number) => {
    try {
      setIsLoading(true);
      const data = await chatApi.getMessages(sessionId);
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      toast.error('Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await chatApi.createSession('New Chat');
      setSessions([newSession, ...sessions]);
      setCurrentSession(newSession);
      setMessages([]);
      toast.success('New chat session created');
    } catch (error) {
      console.error('Failed to create session:', error);
      toast.error('Failed to create chat session');
    }
  };

  const deleteSession = async (sessionId: number) => {
    if (!confirm('Are you sure you want to delete this chat session?')) {
      return;
    }

    try {
      await chatApi.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));

      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }

      toast.success('Chat session deleted');
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error('Failed to delete chat session');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !currentSession || isStreaming) {
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setIsStreaming(true);
    setStreamingMessage('');
    setStreamingCitations([]);

    // Add user message to UI
    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      session_id: currentSession.id,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages([...messages, tempUserMessage]);

    try {
      const token = getToken();
      if (!token) {
        throw new Error('No authentication token');
      }

      // Track accumulated content locally to avoid state timing issues
      let accumulatedContent = '';
      let accumulatedCitations: Citation[] = [];

      // Stream the response
      for await (const chunk of chatApi.streamMessage(
        currentSession.id,
        userMessage,
        token
      )) {
        if (chunk.type === 'content' && chunk.content) {
          accumulatedContent += chunk.content;
          setStreamingMessage(accumulatedContent);
        } else if (chunk.type === 'citation' && chunk.citation) {
          accumulatedCitations.push(chunk.citation);
          setStreamingCitations(accumulatedCitations);
        } else if (chunk.type === 'done') {
          // Finalize the streaming message with accumulated content
          const assistantMessage: ChatMessage = {
            id: Date.now() + 1,
            session_id: currentSession.id,
            role: 'assistant',
            content: accumulatedContent,
            citations: accumulatedCitations.length > 0 ? accumulatedCitations : undefined,
            created_at: new Date().toISOString(),
          };
          setMessages(prev => [...prev, assistantMessage]);
          setStreamingMessage('');
          setStreamingCitations([]);
          break;
        } else if (chunk.type === 'error') {
          toast.error(chunk.error || 'Error generating response');
          setStreamingMessage('');
          setStreamingCitations([]);
          break;
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
      setStreamingMessage('');
      setStreamingCitations([]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <AppShell breadcrumbs={[{ label: 'AI Assistant' }]}>
      <div className="flex h-[calc(100vh-4rem)] bg-white">
        {/* Sidebar - Chat Sessions */}
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <Button onClick={createNewSession} className="w-full">
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {sessions.map(session => (
            <Card
              key={session.id}
              className={`p-3 mb-2 cursor-pointer hover:bg-gray-50 transition-colors ${
                currentSession?.id === session.id ? 'bg-blue-50 border-blue-300' : ''
              }`}
              onClick={() => setCurrentSession(session)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {session.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(session.updated_at).toLocaleDateString()}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="ml-2"
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <h1 className="text-xl font-semibold text-gray-900">
            {currentSession ? currentSession.title : 'Select a chat session'}
          </h1>
          <p className="text-sm text-gray-500">
            AI Legal Assistant powered by Claude
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!currentSession && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-gray-700 mb-2">
                  Welcome to the Legal Assistant
                </h2>
                <p className="text-gray-500 mb-4">
                  Create a new chat session to get started
                </p>
                <Button onClick={createNewSession}>
                  <Plus className="mr-2 h-4 w-4" />
                  New Chat
                </Button>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          )}

          {currentSession && messages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <Card
                className={`max-w-[80%] p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>

                {message.citations && message.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-semibold mb-2 text-gray-600">
                      Sources:
                    </p>
                    <div className="space-y-1">
                      {message.citations.map((citation, idx) => (
                        <div
                          key={idx}
                          className="flex items-center text-xs text-gray-600 hover:text-blue-600 cursor-pointer"
                        >
                          <FileText className="h-3 w-3 mr-1" />
                          <span>
                            {citation.document_title}
                            {citation.page_number && ` (Page ${citation.page_number})`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            </div>
          ))}

          {/* Streaming message */}
          {isStreaming && streamingMessage && (
            <div className="flex justify-start">
              <Card className="max-w-[80%] p-4 bg-white border border-gray-200">
                <div className="whitespace-pre-wrap">{streamingMessage}</div>

                {streamingCitations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-semibold mb-2 text-gray-600">
                      Sources:
                    </p>
                    <div className="space-y-1">
                      {streamingCitations.map((citation, idx) => (
                        <div
                          key={idx}
                          className="flex items-center text-xs text-gray-600"
                        >
                          <FileText className="h-3 w-3 mr-1" />
                          <span>
                            {citation.document_title}
                            {citation.page_number && ` (Page ${citation.page_number})`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-2 flex items-center text-gray-400">
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  <span className="text-xs">Thinking...</span>
                </div>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        {currentSession && (
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <Input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a legal question..."
                disabled={isStreaming}
                className="flex-1"
              />
              <Button
                onClick={sendMessage}
                disabled={!input.trim() || isStreaming}
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

export default function Chat() {
  return (
    <ProtectedRoute>
      <ChatPage />
    </ProtectedRoute>
  );
}
