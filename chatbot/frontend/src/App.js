import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const userToken = localStorage.getItem("userToken"); // JWT token
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await axios.get("/api/history", {
          headers: { Authorization: `Bearer ${userToken}` }
        });
        setMessages(res.data.map(({ message, response }) => [
          { from: "user", text: message },
          { from: "bot", text: response }
        ]).flat());
      } catch (e) { }
    }
    fetchHistory();
  }, [userToken]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages([...messages, { from: "user", text: input }]);
    setLoading(true);
    const res = await axios.post("/api/chat/", {
      message: input,
      channel: "web"
    }, { headers: { Authorization: `Bearer ${userToken}` } });
    setMessages([...messages, { from: "user", text: input }, { from: "bot", text: res.data.response }]);
    setInput("");
    setLoading(false);
  };

  return (
    <div style={{ width: 450, margin: "40px auto", border: "1px solid #ccc", borderRadius: 8, background: "#fafcff" }}>
      <h2>HRMS AI Chatbot (Advanced)</h2>
      <div style={{ minHeight: 250, marginBottom: 10, background: "#f8f8f8", padding: 10, borderRadius: 8 }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.from === "user" ? "right" : "left", margin: "4px 0" }}>
            <b>{msg.from === "user" ? "You" : "Bot"}:</b> {msg.text}
          </div>
        ))}
        {loading && <div><em>Bot is typing...</em></div>}
      </div>
      <input
        style={{ width: "78%" }}
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={e => e.key === "Enter" && sendMessage()}
        disabled={loading}
      />
      <button onClick={sendMessage} disabled={loading}>Send</button>
    </div>
  );
}

export default App;