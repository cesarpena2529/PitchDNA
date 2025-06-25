import React from "react";

export default function VideoModal({ url, open, onClose }) {
  if (!open) return null;
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: 24,
          maxWidth: 800,
          width: "90%",
          position: "relative",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: 12,
            right: 16,
            fontSize: 28,
            background: "none",
            border: "none",
            color: "#333",
            cursor: "pointer",
          }}
        >
          ×
        </button>
        <iframe
          src={url}
          title="Baseball Savant Video"
          width="100%"
          height="400"
          allowFullScreen
          style={{ borderRadius: 8, border: "none" }}
        ></iframe>
      </div>
    </div>
  );
}