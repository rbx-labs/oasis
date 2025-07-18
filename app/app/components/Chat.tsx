"use client";

import React, { useState } from "react";

export default function Chat() {
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>(
    []
  );
  const [input, setInput] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message to chat
    const newMessages = [...messages, { sender: "User", text: input }];
    setMessages(newMessages);
    setInput("");

    try {
      // Send message to LLM endpoint
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL_BASE}/api/v1/llm/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: input }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Add LLM response to chat
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: "LLM", text: data.reply },
        ]);
      } else {
        console.error("Failed to fetch LLM response");
      }
    } catch (error) {
      console.error("Error communicating with LLM endpoint:", error);
    }
  };

  return (
    <div className="mx-auto p-4">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Chat</h2>
        <div className="overflow-y-auto h-64 mb-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`mb-2 ${
                msg.sender === "User" ? "text-right" : "text-left"
              }`}
            >
              <span
                className={`inline-block p-2 rounded-lg ${
                  msg.sender === "User"
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200"
                }`}
              >
                {msg.text}
              </span>
            </div>
          ))}
        </div>
        <div className="flex">
          <input
            type="text"
            className="flex-grow p-2 border rounded-l-lg"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
          />
          <button
            className="p-2 bg-blue-500 text-white rounded-r-lg"
            onClick={handleSend}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
