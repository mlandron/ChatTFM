import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  History,
  Clock,
  User,
  Bot,
  ChevronDown,
  Trash2,
  MessageCircle
} from 'lucide-react'

const ChatHistoryDropdown = ({ onLoadConversation, userId, backendUrl }) => {
  const [conversations, setConversations] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadConversations()
    }
  }, [isOpen])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/chat-history/conversations/${userId}`)
      if (!response.ok) throw new Error('Failed to load conversations')
      
      const data = await response.json()
      if (data.status === 'success') {
        setConversations(data.data)
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteConversation = async (conversationId, e) => {
    e.stopPropagation()
    if (!confirm('¿Eliminar esta conversación?')) return
    
    try {
      const response = await fetch(`${backendUrl}/api/chat-history/conversation/${conversationId}?user_id=${userId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setConversations(prev => prev.filter(conv => conv.conversation_id !== conversationId))
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-ES', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const truncateMessage = (message, maxLength = 50) => {
    if (message.length <= maxLength) return message
    return message.substring(0, maxLength) + '...'
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2"
      >
        <History className="w-4 h-4" />
        Historial
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-background border rounded-lg shadow-lg z-50 max-h-96 overflow-hidden">
          <div className="p-3 border-b">
            <h3 className="font-semibold text-sm">Conversaciones Recientes</h3>
            <p className="text-xs text-muted-foreground">
              {conversations.length} conversaciones
            </p>
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                <p className="text-sm text-muted-foreground mt-2">Cargando...</p>
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center">
                <MessageCircle className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No hay conversaciones</p>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {conversations.slice(0, 10).map((conversation) => (
                  <div
                    key={conversation.conversation_id}
                    className="flex items-center gap-3 p-2 rounded-md hover:bg-muted cursor-pointer transition-colors"
                    onClick={() => {
                      onLoadConversation(conversation.conversation_id)
                      setIsOpen(false)
                    }}
                  >
                    <div className="flex-shrink-0">
                      {conversation.last_message_sender === 'user' ? (
                        <User className="w-4 h-4 text-primary" />
                      ) : (
                        <Bot className="w-4 h-4 text-green-600" />
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="secondary" className="text-xs">
                          {conversation.last_message_sender === 'user' ? 'Tú' : 'Bot'}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(conversation.last_message_time)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {truncateMessage(conversation.last_message)}
                      </p>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => deleteConversation(conversation.conversation_id, e)}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatHistoryDropdown 