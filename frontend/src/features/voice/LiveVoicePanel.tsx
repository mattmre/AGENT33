import { useState } from "react";

export function LiveVoicePanel({ token }: { token: string | null }): JSX.Element {
    const [isActive, setIsActive] = useState(false);

    async function toggleConnection() {
        setIsActive(!isActive);
        // In a complete implementation, we would use:
        // import { LiveKitRoom, RoomAudioRenderer, VoiceAssistantControlBar } from "@livekit/components-react";
        // And request a token from our backend to join the specific room.
    }

    return (
        <div className="live-voice-panel" style={{
            background: "linear-gradient(170deg, rgba(22, 45, 58, 0.9), rgba(10, 27, 36, 0.92))",
            border: "1px solid #30d5c8",
            borderRadius: "14px",
            padding: "0.95rem",
            boxShadow: "0 18px 34px rgba(5, 13, 17, 0.45)",
            display: "grid",
            gap: "0.8rem"
        }}>
            <h2 style={{ margin: 0, fontSize: "1.02rem", color: "#30d5c8" }}>🎙️ Live Voice Orchestrator</h2>
            <p style={{ margin: "0.3rem 0 0.7rem", color: "#9dc3cf", fontSize: "0.85rem" }}>
                Connect via WebRTC for an ultra-low-latency, interruptible voice conversation with AGENT-33.
            </p>

            <div className="voice-controls" style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                <button
                    onClick={toggleConnection}
                    disabled={!token}
                    style={{
                        background: isActive ? "#ff6b6b" : "linear-gradient(120deg, #1d3746, #36586a 40%, #5d6a3a 100%)",
                        color: "#fff",
                        fontWeight: "bold",
                        padding: "0.55rem 0.9rem",
                        border: "1px solid #6f5c31",
                        borderRadius: "10px",
                        cursor: token ? "pointer" : "not-allowed"
                    }}
                >
                    {isActive ? "Disconnect" : "Connect Microphone"}
                </button>

                {isActive && (
                    <div className="audio-visualizer" style={{ display: "flex", gap: "4px", alignItems: "flex-end", height: "24px" }}>
                        <span className="bar" style={{ width: "4px", height: "12px", background: "#8be9a8", display: "inline-block" }}></span>
                        <span className="bar" style={{ width: "4px", height: "20px", background: "#8be9a8", display: "inline-block", animation: "pulse 1s infinite alternate" }}></span>
                        <span className="bar" style={{ width: "4px", height: "8px", background: "#8be9a8", display: "inline-block" }}></span>
                        <span style={{ fontSize: "0.8rem", color: "#8be9a8", marginLeft: "8px" }}>Listening...</span>
                    </div>
                )}
            </div>
        </div>
    );
}
