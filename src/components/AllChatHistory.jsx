import { useEffect, useState } from 'react';

export default function AllChatHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/admin/all-chat-history')
      .then(res => res.json())
      .then(data => {
        setHistory(data.data || []);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load chat history');
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-500">{error}</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">All Chat History (Admin)</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full border text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="border px-2 py-1">User ID</th>
              <th className="border px-2 py-1">Conversation ID</th>
              <th className="border px-2 py-1">Sender</th>
              <th className="border px-2 py-1">Message</th>
              <th className="border px-2 py-1">Created At</th>
            </tr>
          </thead>
          <tbody>
            {history.map(msg => (
              <tr key={msg.id}>
                <td className="border px-2 py-1">{msg.user_id}</td>
                <td className="border px-2 py-1">{msg.conversation_id}</td>
                <td className="border px-2 py-1">{msg.sender}</td>
                <td className="border px-2 py-1 max-w-xs truncate">{msg.message_content}</td>
                <td className="border px-2 py-1">{msg.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 