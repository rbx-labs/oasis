"use client";

import React, { useState, useRef, useEffect } from "react";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<
    Array<{ role: string; content: string }>
  >([
    {
      role: "assistant",
      content:
        "우리집에 오신것을 환영합니다! 개발에 관한 궁금한 점이 있으시면 무엇이든 도와드릴게요",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage = { role: "user", content: message };
    setChatHistory((prev) => [...prev, newMessage]);
    setIsLoading(true);
    setMessage("");

    try {
      const response = await fetch("/llm/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "qwen2.5",
          messages: [
            { role: "system", content: "너는 집사입니다" },
            ...chatHistory,
            newMessage,
          ],
          stream: true,
        }),
      });

      const reader = response.body?.getReader();
      let partialMessage = "";

      if (reader) {
        setChatHistory((prev) => [...prev, { role: "assistant", content: "" }]);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const body = JSON.parse(new TextDecoder().decode(value));
          partialMessage += body.message.content;

          setChatHistory((prev) => {
            const newHistory = [...prev];
            newHistory[newHistory.length - 1] = {
              role: "assistant",
              content: partialMessage,
            };
            return newHistory;
          });
        }
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div
        ref={chatContainerRef}
        className="bg-white rounded-lg shadow-lg p-4 mb-4 h-[400px] overflow-y-auto"
      >
        {chatHistory.map((msg, index) => (
          <div
            key={index}
            className={`mb-4 p-3 rounded-lg ${
              msg.role === "user" ? "bg-blue-100 ml-auto" : "bg-gray-100"
            } max-w-[80%] ${msg.role === "user" ? "ml-auto" : "mr-auto"}`}
          >
            {msg.content}
          </div>
        ))}
        {isLoading && (
          <div className="text-center text-gray-500">AI is thinking...</div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
          placeholder="Type your message..."
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
        >
          Send
        </button>
      </form>
    </div>
  );
}
