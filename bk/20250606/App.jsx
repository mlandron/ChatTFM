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
import { Send, Settings, MessageCircle, Database, Loader2, FileText, Bot, User } from 'lucide-react'
import './App.css'

// New Sub-component for rendering a single chat message
const ChatMessage = ({ message, formatTimestamp }) => {
  const isBot = message.type === 'bot';

  return (
    <div className={`flex items-start gap-3 ${isBot ? 'justify-start' : 'justify-end'}`}>
      {isBot && <div className="p-2 rounded-full bg-muted"><Bot className="w-5 h-5 text-primary" /></div>}
      
      <div className={`max-w-[85%] rounded-lg p-3.5 ${
        isBot ? 'bg-muted text-foreground' : 'bg-primary text-primary-foreground'
      }`}>
        <div className="whitespace-pre-wrap text-sm">{message.content}</div>
        <div className={`text-xs opacity-70 mt-2 text-right ${isBot ? 'text-foreground' : 'text-primary-foreground'}`}>
          {formatTimestamp(message.timestamp)}
        </div>
        
        {/* CRITICAL CHANGE: Correctly display source documents using source */}
        {isBot && message.sourceDocuments && message.sourceDocuments.length > 0 && (
          <div className="mt-3 pt-3 border-t border-t-background/50">
            <h4 className="text-xs font-semibold mb-2">Fuentes Consultadas:</h4>
            <div className="flex flex-wrap gap-2">
              {message.sourceDocuments.map((doc, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs font-normal">
                  <FileText className="w-3 h-3 mr-1.5" />
                  {doc.source || 'N/A'}
                </Badge>
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
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  
  // Parameter state
  const [embeddingModel, setEmbeddingModel] = useState('BAAI/bge-m3');
  const [topK, setTopK] = useState(10);
  const [temperature, setTemperature] = useState(0.1);
  const [chatModel, setChatModel] = useState('gpt-4o-mini');
  const [showSettings, setShowSettings] = useState(false);
  
  const BACKEND_URL = process.env.NODE_ENV === 'production' 
    ? 'https://chattfm.onrender.com' 
    : 'http://localhost:5001';
  
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);
  
  useEffect(() => {
    testConnection();
    // Add a welcome message
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
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: inputMessage,
          embedding_model: embeddingModel,
          top_k: topK, // chat.py will use this for both vector_top_k and bm25_top_k
          temperature: temperature,
          chat_model: chatModel
        })
      });
      
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer || data.error || 'Lo siento, he encontrado un error.',
        timestamp: new Date(),
        sourceDocuments: data.source_documents || [],
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Fetch error:", error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'No pude conectarme al servicio. Por favor, revisa la conexión y la consola para más detalles.',
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
  
  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div className="app-container min-h-screen bg-muted/20 p-2 sm:p-4">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-4 h-[97vh]">
        
        {/* Settings Panel */}
        <Card className={`lg:col-span-1 ${showSettings ? 'block' : 'hidden lg:block'} flex flex-col`}>
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
          <CardContent className="flex-1 space-y-6 overflow-y-auto pr-2">
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
        </Card>
        
        {/* Chat Panel */}
        <Card className="lg:col-span-3 h-full flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-6 h-6 text-primary" />
                Asistente de Pensiones
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowSettings(!showSettings)} className="lg:hidden">
                <Settings className="w-5 h-5" />
              </Button>
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
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu pregunta aquí..."
                disabled={isLoading}
                className="flex-1"
              />
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