import { useState } from "react";

const API_URL = "https://ai-crm-vazc.onrender.com";

function Chat() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm your AI CRM assistant. Ask me about customers, deals, notes, or sales activity.",
    },
  ]);

  const [loading, setLoading] = useState(false);

  const sendMessage = async (event) => {
    event.preventDefault();

    const trimmedMessage = message.trim();

    if (!trimmedMessage || loading) {
      return;
    }

    const userMessage = {
      role: "user",
      content: trimmedMessage,
    };

    setMessages((previous) => [...previous, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmedMessage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.message || "Action completed.",
          toolCalls: data.tool_calls || [],
          actionPerformed: data.action_performed || false,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: `Error: ${error.message}`,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="chat-card">
      <div className="chat-header">
        <div>
          <h2>AI Assistant</h2>
          <p>Ask questions or perform CRM actions</p>
        </div>

        <span className="online-indicator">
          <span></span>
          Online
        </span>
      </div>

      <div className="messages">
        {messages.map((item, index) => (
          <div
            key={index}
            className={`message-row ${item.role}`}
          >
            <div
              className={`message ${
                item.error ? "message-error" : ""
              }`}
            >
              <div className="message-role">
                {item.role === "user" ? "You" : "AI Assistant"}
              </div>

              <div className="message-content">
                {item.content}
              </div>

              {item.actionPerformed && (
                <div className="action-success">
                  ✓ CRM action completed successfully
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="message">
              <div className="message-role">AI Assistant</div>

              <div className="typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-area" onSubmit={sendMessage}>
        <input
          type="text"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask about customers, deals, or sales..."
          disabled={loading}
        />

        <button type="submit" disabled={loading || !message.trim()}>
          {loading ? "..." : "Send"}
        </button>
      </form>
    </section>
  );
}

export default Chat;