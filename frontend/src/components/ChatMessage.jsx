import React from "react";

const ChatMessage = ({ message }) => {
  const isAgent = message.sender === "agent";
  return (
    <div className={`chat-message-container ${isAgent ? "agent" : "user"}`}>
      <div className="chat-avatar">
        {isAgent ? "🤖" : "👤"}
      </div>
      <div className={`chat-bubble ${isAgent ? "agent" : "user"} ${message.isError ? "error" : ""}`}>
        <div className="chat-sender-name">
          {isAgent ? "CRM Assistant" : "You"}
        </div>
        <div className="chat-text">
          {message.text.split("\n").map((line, idx) => (
            <p key={idx} style={{ margin: "0 0 8px 0" }}>
              {line}
            </p>
          ))}
        </div>
        <div className="chat-time">
          {message.timestamp}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
