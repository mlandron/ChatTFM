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
import { Send, Settings, MessageCircle, Database, Loader2 } from 'lucide-react'
import './App.css'

function App() {
  // Chat state
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('unknown')
  
  // Parameter state
  const [embeddingModel, setEmbeddingModel] = useState('BAAI/bge-m3')
  const [topK, setTopK] = useState(5)
  const [temperature, setTemperature] = useState(0.1)
  const [chatModel, setChatModel] = useState('gpt-4o-mini')
  const [showSettings, setShowSettings] = useState(false)
  
  // Backend URL - update this for production
  const BACKEND_URL = process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-url.vercel.app' 
    : 'http://localhost:5001'
  
  const messagesEndRef = useRef(null)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  useEffect(() => {
    // Test connection on component mount
    testConnection()
  }, [])
  
  const testConnection = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/test-connection`)
      const data = await response.json()
      setConnectionStatus(data.status === 'success' ? 'connected' : 'error')
    } catch (error) {
      setConnectionStatus('error')
    }
  }
  
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputMessage,
          embedding_model: embeddingModel,
          top_k: topK,
          temperature: temperature,
          chat_model: chatModel
        })
      })
      
      const data = await response.json()
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer || data.error || 'Sorry, I encountered an error.',
        timestamp: new Date(),
        sourceDocuments: data.source_documents || [],
        parametersUsed: data.parameters_used || {}
      }
      
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I could not connect to the backend service. Please check your connection.',
        timestamp: new Date(),
        sourceDocuments: [],
        parametersUsed: {}
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
  
  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-6 h-screen max-h-screen">
        
        {/* Settings Panel */}
        <div className={`lg:col-span-1 ${showSettings ? 'block' : 'hidden lg:block'}`}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Parameters
              </CardTitle>
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                <span className="text-sm">Supabase</span>
                <Badge variant={connectionStatus === 'connected' ? 'default' : 'destructive'}>
                  {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Embedding Model */}
              <div className="space-y-2">
                <Label htmlFor="embedding-model">Embedding Model</Label>
                <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BAAI/bge-m3">BAAI/bge-m3 (Default)</SelectItem>
                    <SelectItem value="text-embedding-3-small">OpenAI text-embedding-3-small</SelectItem>
                    <SelectItem value="text-embedding-3-large">OpenAI text-embedding-3-large</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {/* Top K */}
              <div className="space-y-2">
                <Label htmlFor="top-k">Top K: {topK}</Label>
                <Slider
                  value={[topK]}
                  onValueChange={(value) => setTopK(value[0])}
                  max={20}
                  min={0}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>0</span>
                  <span>20</span>
                </div>
              </div>
              
              {/* Temperature */}
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature: {temperature}</Label>
                <Slider
                  value={[temperature]}
                  onValueChange={(value) => setTemperature(value[0])}
                  max={1}
                  min={0.01}
                  step={0.01}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>0.01</span>
                  <span>1.0</span>
                </div>
              </div>
              
              {/* Chat Model */}
              <div className="space-y-2">
                <Label htmlFor="chat-model">ChatGPT Model</Label>
                <Select value={chatModel} onValueChange={setChatModel}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4o-mini">GPT-4o Mini (Default)</SelectItem>
                    <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                    <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Button 
                onClick={testConnection} 
                variant="outline" 
                className="w-full"
                disabled={isLoading}
              >
                Test Connection
              </Button>
              
            </CardContent>
          </Card>
        </div>
        
        {/* Chat Panel */}
        <div className="lg:col-span-3">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5" />
                  RAG Chatbot
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSettings(!showSettings)}
                  className="lg:hidden"
                >
                  <Settings className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            
            {/* Messages Area */}
            <CardContent className="flex-1 flex flex-col min-h-0">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  {messages.length === 0 && (
                    <div className="text-center text-gray-500 py-8">
                      <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Welcome to the RAG Chatbot!</p>
                      <p className="text-sm">Ask me anything and I'll search through the knowledge base.</p>
                    </div>
                  )}
                  
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.type === 'user'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        <div className="text-xs opacity-70 mt-1">
                          {formatTimestamp(message.timestamp)}
                        </div>
                        
                        {/* Source Documents */}
                        {message.sourceDocuments && message.sourceDocuments.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-300">
                            <div className="text-xs font-semibold mb-1">Sources:</div>
                            <div className="space-y-1">
                              {message.sourceDocuments.slice(0, 3).map((doc, idx) => (
                                <div key={idx} className="text-xs bg-white bg-opacity-50 p-1 rounded">
                                  {doc.content.substring(0, 100)}...
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Parameters Used */}
                        {message.parametersUsed && Object.keys(message.parametersUsed).length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-300">
                            <div className="text-xs font-semibold mb-1">Parameters:</div>
                            <div className="text-xs space-x-2">
                              <Badge variant="secondary" className="text-xs">
                                Model: {message.parametersUsed.chat_model}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                Top-K: {message.parametersUsed.top_k}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                Temp: {message.parametersUsed.temperature}
                              </Badge>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg p-3 flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
              
              {/* Input Area */}
              <Separator className="my-4" />
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button 
                  onClick={sendMessage} 
                  disabled={isLoading || !inputMessage.trim()}
                  size="icon"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default App

