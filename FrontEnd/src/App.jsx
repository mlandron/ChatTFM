import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Slider } from '@/components/ui/slider.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Send, Settings, MessageCircle, Database, Loader2, FileText, Bot, User, Sun, Moon, History, Plus } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import ChatHistory from './components/ChatHistory.jsx'
import ChatHistoryModal from './components/ChatHistoryModal.jsx'
import './App.css'

// ===================================================================
// 1. CHAT MESSAGE SUB-COMPONENT
// ===================================================================
// This new component handles rendering a single message, making the code much cleaner.
const ChatMessage = ({ message }) => {
  const isBot = message.type === 'bot';
  // It correctly reads the sourceDocuments array from the message object.
  const sourceDocuments = message.sourceDocuments || [];

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    // This div handles the left/right alignment.
    <div className={`flex items-start gap-3 ${isBot ? 'justify-start' : 'justify-end'}`}>
      
      {/* Bot Icon - Only show for bot messages on the left */}
      {isBot && <div className="p-2 rounded-full bg-muted border"><Bot className="w-5 h-5 text-primary" /></div>}
      
      {/* Message Bubble with theme-aware colors */}
      <div className={`max-w-[85%] rounded-lg p-3.5 ${isBot ? 'bg-card border' : 'bg-primary text-primary-foreground'}`}>
        <div className={`chat-markdown ${isBot ? 'text-left' : 'text-right'}`}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Custom styling for different markdown elements
              a: ({ children, href }) => (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  {children}
                </a>
              ),
              code: ({ node, inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="div"
                    className="rounded-lg"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono" {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <div className={`text-xs opacity-70 mt-2 ${isBot ? 'text-right text-muted-foreground' : 'text-left text-primary-foreground/80'}`}>
          {formatTimestamp(message.timestamp)}
        </div>
        
        {/* Correctly renders clickable source document links */}
        {isBot && sourceDocuments.length > 0 && (
          <div className="mt-3 pt-3 border-t border-t-border/50 text-left">
            <h4 className="text-xs font-semibold mb-2">Fuentes Consultadas:</h4>
            <div className="flex flex-wrap gap-2">
              {sourceDocuments.map((doc, idx) => (
                <a 
                  key={idx} 
                  href={doc.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="no-underline"
                >
                  <Badge variant="secondary" className="text-xs font-normal cursor-pointer hover:bg-secondary/80">
                    <FileText className="w-3 h-3 mr-1.5" />
                    {doc.source_name}
                  </Badge>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Icon - Only show for user messages on the right */}
      {!isBot && <div className="p-2 rounded-full bg-muted border"><User className="w-5 h-5" /></div>}
    </div>
  );
};


// ===================================================================
// 2. MAIN APP COMPONENT
// ===================================================================
function App() {
  const [theme, setTheme] = useState('light');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  
  // Chat history state
  const [currentUserId, setCurrentUserId] = useState('anonymous');
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  
  const [embeddingModel, setEmbeddingModel] = useState('BAAI/bge-m3');
  const [topK, setTopK] = useState(10);
  const [temperature, setTemperature] = useState(0.1);
  const [chatModel, setChatModel] = useState('gpt-4o');
  const [showSettings, setShowSettings] = useState(false);
  
  const BACKEND_URL = process.env.NODE_ENV === 'production' 
    ? import.meta.env.VITE_BACKEND_URL || 'https://chat-tfm.vercel.app'
    : 'http://localhost:5001';
  
  const messagesEndRef = useRef(null);
  
  // Effect to apply the theme (light/dark)
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);
  
  // Initialize with a welcome message and test connection
  useEffect(() => {
    // Generate a unique user ID for this session
    const userId = localStorage.getItem('chatbot_user_id') || `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chatbot_user_id', userId);
    setCurrentUserId(userId);
    
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: `# ¡Hola! 👋

Soy tu **asistente RAG** especializado en el sistema de pensiones dominicano.

## ¿Qué puedo hacer?

- Responder preguntas sobre **pensiones**
- Explicar **procedimientos** del sistema
- Proporcionar información sobre **beneficios**
- Ayudar con **requisitos** y documentación

> 💡 **Tip**: Puedes hacer preguntas como:
> - "¿Cuáles son los requisitos para pensionarse?"
> - "¿Cómo funciona el cálculo de pensión?"
> - "¿Qué documentos necesito para una pensión de sobrevivencia?"



¡Hazme una pregunta sobre el sistema de pensiones dominicano!`,
      timestamp: new Date()
    }]);
    testConnection();
  }, []);
  
  const testConnection = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/test-connection`);
      if (!response.ok) throw new Error("Connection failed");
      const data = await response.json();
      setConnectionStatus(data.status === 'success' ? 'connected' : 'error');
    } catch (error) {
      setConnectionStatus('error');
    }
  };
  
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: inputMessage,
          user_id: currentUserId,
          conversation_id: currentConversationId,
          embedding_model: embeddingModel,
          top_k: topK,
          temperature: temperature,
          chat_model: chatModel
        })
      });

      if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
      
      const data = await response.json();
      
      // Update conversation ID if it's a new conversation
      if (data.conversation_id && !currentConversationId) {
        setCurrentConversationId(data.conversation_id);
      }
      
      // This correctly attaches the source documents to the message object
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer || 'Lo siento, he encontrado un error.',
        timestamp: new Date(),
        sourceDocuments: data.source_documents || [],
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'No pude conectarme al servicio. Por favor, revisa la conexión.',
        timestamp: new Date(),
        sourceDocuments: [],
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: `# ¡Hola! 👋

Soy tu **asistente RAG** especializado en el sistema de pensiones dominicano.

## ¿Qué puedo hacer?

- Responder preguntas sobre **pensiones**
- Explicar **procedimientos** del sistema
- Proporcionar información sobre **beneficios**
- Ayudar con **requisitos** y documentación

> 💡 **Tip**: Puedes hacer preguntas como:
> - "¿Cuáles son los requisitos para pensionarse?"
> - "¿Cómo funciona el cálculo de pensión?"
> - "¿Qué documentos necesito para una pensión de sobrevivencia?"



¡Hazme una pregunta sobre el sistema de pensiones dominicano!`,
      timestamp: new Date()
    }]);
    setShowHistory(false);
  };

  const loadConversation = async (conversationId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat-history/conversation/${conversationId}/messages?user_id=${currentUserId}`);
      if (!response.ok) throw new Error('Failed to load conversation');
      
      const data = await response.json();
      if (data.status === 'success') {
        // Convert database messages to frontend format
        const convertedMessages = data.data.map(msg => ({
          id: msg.id,
          type: msg.sender,
          content: msg.message_content,
          timestamp: new Date(msg.created_at)
        }));
        
        setMessages(convertedMessages);
        setCurrentConversationId(conversationId);
        setShowHistory(false);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };
  
  return (
    <div className="min-h-screen bg-muted/30 p-2 sm:p-4 font-sans">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-4 h-[97vh]">
        
        {/* Settings Panel */}
        <div className={`lg:col-span-1 ${showSettings ? 'block' : 'hidden lg:block'}`}>
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <Settings className="w-5 h-5" />
                Parámetros
              </CardTitle>
              <div className="flex items-center gap-2 pt-2">
                <Database className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-semibold">Supabase</span>
                <Badge variant={connectionStatus === 'connected' ? 'success' : 'destructive'}>
                  {connectionStatus}
                </Badge>
              </div>
            </CardHeader>
            <ScrollArea className="flex-1">
              <CardContent className="space-y-6 p-6">
                {/* Chat History Section */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-semibold">Historial de Chat</Label>
                    <Button variant="ghost" size="icon" onClick={() => setShowHistoryModal(true)}>
                      <History className="w-4 h-4" />
                    </Button>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={startNewConversation}
                    className="w-full"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Nueva Conversación
                  </Button>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <Label htmlFor="embedding-model">Modelo de Embedding</Label>
                  <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BAAI/bge-m3">BAAI/bge-m3</SelectItem>
                      <SelectItem value="text-embedding-3-small">OpenAI Small</SelectItem>
                      <SelectItem value="text-embedding-3-large">OpenAI Large</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="top-k">Top K: {topK}</Label>
                  <Slider value={[topK]} onValueChange={(v) => setTopK(v[0])} max={20} min={1} step={1} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperatura: {temperature}</Label>
                  <Slider value={[temperature]} onValueChange={(v) => setTemperature(v[0])} max={1} min={0.01} step={0.01} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="chat-model">Modelo de Chat</Label>
                  <Select value={chatModel} onValueChange={setChatModel}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                      <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                      <SelectItem value="gpt-4">GPT-4</SelectItem>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </ScrollArea>
          </Card>
        </div>
        
        {/* Chat Panel */}
        <div className="lg:col-span-3">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-6 h-6 text-primary" />
                  Asistente de Pensiones
                </div>
                <div className="flex items-center gap-2">
                  {/* Dark Mode Toggle */}
                  <Button variant="ghost" size="icon" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                    <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                    <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                    <span className="sr-only">Toggle theme</span>
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setShowSettings(!showSettings)} className="lg:hidden">
                    <Settings className="w-5 h-5" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0">
              <ScrollArea className="flex-1 pr-4 -mr-4">
                <div className="space-y-6">
                  {/* The mapping now uses the clean ChatMessage component */}
                  {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                  ))}
                  
                  {/* Improved loading indicator */}
                  {isLoading && (
                    <div className="flex items-start gap-3 justify-start">
                       <div className="p-2 rounded-full bg-muted border"><Bot className="w-5 h-5 text-primary" /></div>
                       <div className="bg-card border rounded-lg p-3.5 flex items-center gap-2">
                         <Loader2 className="w-4 h-4 animate-spin" />
                         <span className="text-sm text-muted-foreground">Pensando...</span>
                       </div>
                   </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
              
              <Separator className="my-4" />
              <div className="flex items-center gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Escribe tu mensaje..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()} size="icon" aria-label="Send Message">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Chat History Modal */}
      <ChatHistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        onLoadConversation={(conversationId) => {
          loadConversation(conversationId);
          setShowHistoryModal(false);
        }}
        userId={currentUserId}
        backendUrl={BACKEND_URL}
      />
    </div>
  )
}

export default App