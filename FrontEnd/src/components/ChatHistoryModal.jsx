import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  MessageCircle, 
  Clock, 
  User, 
  Bot, 
  ArrowLeft, 
  Trash2,
  History,
  Calendar,
  X,
  Search,
  Filter
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import { Input } from '@/components/ui/input.jsx'

const ChatHistoryModal = ({ isOpen, onClose, onLoadConversation, userId, backendUrl }) => {
  const [conversations, setConversations] = useState([])
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [conversationMessages, setConversationMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filter, setFilter] = useState('all') // all, user, bot

  useEffect(() => {
    if (isOpen) {
      loadConversations()
    }
  }, [isOpen])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/chat-history/conversations/${userId}`)
      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment and try again.')
        }
        throw new Error('Failed to load conversations')
      }
      
      const data = await response.json()
      if (data.status === 'success') {
        setConversations(data.data)
      } else {
        throw new Error(data.message || 'Failed to load conversations')
      }
    } catch (error) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const loadConversationMessages = async (conversationId) => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/chat-history/conversation/${conversationId}/messages?user_id=${userId}`)
      if (!response.ok) throw new Error('Failed to load conversation')
      
      const data = await response.json()
      if (data.status === 'success') {
        setConversationMessages(data.data)
        setSelectedConversation(conversationId)
      } else {
        throw new Error(data.message || 'Failed to load conversation')
      }
    } catch (error) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const deleteConversation = async (conversationId) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta conversación?')) return
    
    try {
      const response = await fetch(`${backendUrl}/api/chat-history/conversation/${conversationId}?user_id=${userId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        // Remove from conversations list
        setConversations(prev => prev.filter(conv => conv.conversation_id !== conversationId))
        if (selectedConversation === conversationId) {
          setSelectedConversation(null)
          setConversationMessages([])
        }
      }
    } catch (error) {
      setError('Failed to delete conversation')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatTime = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const truncateMessage = (message, maxLength = 100) => {
    if (message.length <= maxLength) return message
    return message.substring(0, maxLength) + '...'
  }

  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = conv.last_message.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filter === 'all' || conv.last_message_sender === filter
    return matchesSearch && matchesFilter
  })

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-lg w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <History className="w-6 h-6 text-primary" />
            <div>
              <h2 className="text-xl font-semibold">Historial de Chat</h2>
              <p className="text-sm text-muted-foreground">
                {conversations.length} conversaciones encontradas
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="p-6 border-b space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Buscar en conversaciones..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background"
            >
              <option value="all">Todos los mensajes</option>
              <option value="user">Solo mis mensajes</option>
              <option value="bot">Solo respuestas del bot</option>
            </select>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {loading && conversations.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <History className="w-8 h-8 mx-auto mb-2 animate-spin" />
                <p className="text-muted-foreground">Cargando historial...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-destructive mb-2">Error: {error}</p>
                <Button onClick={loadConversations} variant="outline">
                  Reintentar
                </Button>
              </div>
            </div>
          ) : selectedConversation ? (
            <div className="h-full flex flex-col">
              {/* Conversation Header */}
              <div className="flex items-center justify-between p-4 border-b">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon" onClick={() => setSelectedConversation(null)}>
                    <ArrowLeft className="w-4 h-4" />
                  </Button>
                  <div>
                    <h3 className="font-semibold">Conversación</h3>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(conversationMessages[0]?.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => onLoadConversation(selectedConversation)}
                  >
                    Continuar
                  </Button>
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => deleteConversation(selectedConversation)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {conversationMessages.map((message) => (
                    <div key={message.id} className={`flex items-start gap-3 ${message.sender === 'bot' ? 'justify-start' : 'justify-end'}`}>
                      {message.sender === 'bot' && (
                        <div className="p-2 rounded-full bg-muted border">
                          <Bot className="w-4 h-4 text-primary" />
                        </div>
                      )}
                      
                      <div className={`max-w-[85%] rounded-lg p-3 ${message.sender === 'bot' ? 'bg-card border' : 'bg-primary text-primary-foreground'}`}>
                        <div className="chat-markdown">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
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
                            {message.message_content}
                          </ReactMarkdown>
                        </div>
                        <div className={`text-xs opacity-70 mt-2 ${message.sender === 'bot' ? 'text-right text-muted-foreground' : 'text-left text-primary-foreground/80'}`}>
                          {formatTime(message.created_at)}
                        </div>
                      </div>

                      {message.sender === 'user' && (
                        <div className="p-2 rounded-full bg-muted border">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          ) : (
            <ScrollArea className="h-full">
              {filteredConversations.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <History className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-semibold mb-2">No hay conversaciones</h3>
                    <p className="text-muted-foreground">
                      {searchTerm ? 'No se encontraron conversaciones con tu búsqueda.' : 'Comienza una nueva conversación para ver tu historial aquí.'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  {filteredConversations.map((conversation) => (
                    <Card 
                      key={conversation.conversation_id} 
                      className="cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => loadConversationMessages(conversation.conversation_id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="secondary" className="text-xs">
                                {conversation.last_message_sender === 'user' ? 'Tú' : 'Bot'}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(conversation.last_message_time)}
                              </span>
                              <Badge variant="outline" className="text-xs">
                                {conversation.message_count} mensajes
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {truncateMessage(conversation.last_message)}
                            </p>
                          </div>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteConversation(conversation.conversation_id)
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatHistoryModal 