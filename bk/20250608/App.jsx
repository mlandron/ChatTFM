import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Slider } from '@/components/ui/slider.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Send, Settings, MessageCircle, Database, Loader2, FileText, Bot, User, Sun, Moon } from 'lucide-react'
import './App.css'

// This sub-component is correct and expects `message.sourceDocuments`
const ChatMessage = ({ message, formatTimestamp }) => {
  const isBot = message.type === 'bot';
  // This correctly expects an array of objects with `source_name` and `url`
  const sourceDocuments = message.sourceDocuments || [];

  return (
    <div className={`flex items-start gap-3 ${isBot ? 'justify-start' : 'justify-end'}`}>
      {isBot && <div className="p-2 rounded-full bg-muted"><Bot className="w-5 h-5 text-primary" /></div>}
      <div className={`max-w-[85%] rounded-lg p-3.5 ${isBot ? 'bg-background' : 'bg-primary text-primary-foreground'}`}>
        <div className="whitespace-pre-wrap text-sm">{message.content}</div>
        <div className={`text-xs opacity-70 mt-2 text-right ${isBot ? 'text-muted-foreground' : 'text-primary-foreground/80'}`}>
          {formatTimestamp(message.timestamp)}
        </div>
        
        {/* This block creates clickable links with icons */}
        {isBot && sourceDocuments.length > 0 && (
          <div className="mt-3 pt-3 border-t border-t-border/50">
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
      {!isBot && <div className="p-2 rounded-full bg-muted"><User className="w-5 h-5" /></div>}
    </div>
  );
};
// Main App Component
function App() {
  const [theme, setTheme] = useState('light');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  const [embeddingModel, setEmbeddingModel] = useState('BAAI/bge-m3');
  const [topK, setTopK] = useState(10);
  const [temperature, setTemperature] = useState(0.1);
  const [chatModel, setChatModel] = useState('gpt-4o-mini');
  const [showSettings, setShowSettings] = useState(false);
  const BACKEND_URL = process.env.NODE_ENV === 'production' ? 'https://chattfm.onrender.com' : 'http://localhost:5001';
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); };
  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  useEffect(() => {
    testConnection();
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: '¡Hola! Soy tu asistente RAG. Pregúntame sobre el sistema de pensiones y buscaré la información en mis documentos.',
      timestamp: new Date()
    }]);
  }, []);

  const testConnection = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/test-connection`);
      const data = await response.json();
      setConnectionStatus(data.status === 'success' ? 'connected' : 'error');
    } catch (error) {
      setConnectionStatus('error');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    const userMessage = { id: Date.now(), type: 'user', content: inputMessage, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: inputMessage, embedding_model: embeddingModel, top_k: topK, temperature: temperature, chat_model: chatModel })
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer || 'Lo siento, he encontrado un error.',
        timestamp: new Date(),
        // --- THIS IS THE CRITICAL LINE ---
        // This ensures the sources received from the backend are attached to the message object.
        sourceDocuments: data.source_documents || [],
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Fetch error:", error);
      const errorMessage = { id: Date.now() + 1, type: 'bot', content: 'No pude conectarme al servicio. Por favor, revisa la conexión y la consola para más detalles.', timestamp: new Date(), sourceDocuments: [] };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };
  const formatTimestamp = (timestamp) => timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="app-container min-h-screen bg-background p-2 sm:p-4">
       {/* --- ADD THIS LINE EXACTLY AS IT IS --- */}
       <h1 style={{color: 'red', fontSize: '40px', position: 'fixed', top: '10px', left: '10px', zIndex: 9999}}>
        TESTING FILE LOAD
      </h1>
      {/* The rest of the JSX is unchanged and correct */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-4 h-[97vh]">
        <Card className={`lg:col-span-1 ${showSettings ? 'block' : 'hidden lg:block'} flex flex-col`}>
          {/* Settings Panel */}
        </Card>
        <Card className="lg:col-span-3 h-full flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-6 h-6 text-primary" />
                Asistente de Pensiones
              </div>
              <div className="flex items-center gap-2">
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
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} formatTimestamp={formatTimestamp} />
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-full bg-muted"><Bot className="w-5 h-5 text-primary" /></div>
                      <div className="bg-muted rounded-lg p-3.5 flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Pensando...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            <Separator className="my-4" />
            <div className="flex items-center gap-2">
              <Input value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyPress={handleKeyPress} placeholder="Escribe tu pregunta aquí..." disabled={isLoading} className="flex-1" />
              <Button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()} size="icon">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;