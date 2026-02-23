import { useState } from "react";

export function MessagingSetup(): JSX.Element {
    const [telegramToken, setTelegramToken] = useState("");
    const [discordToken, setDiscordToken] = useState("");
    const [signalUrl, setSignalUrl] = useState("");
    const [iMessageUrl, setIMessageUrl] = useState("");

    const handleSave = (platform: string) => {
        // In a real app, this would POST to the backend configuration endpoint
        console.log(`Saved ${platform} config`);
        alert(`${platform} configuration saved!`);
    };

    return (
        <div className="messaging-setup">
            <div className="setup-header">
                <h2>Messaging Integrations</h2>
                <p>Connect your agent to external messaging platforms to chat from anywhere.</p>
            </div>

            <div className="setup-grid">
                {/* Telegram Card */}
                <div className="setup-card">
                    <div className="card-icon telegram-icon">📱</div>
                    <h3>Telegram</h3>
                    <p>Connect via official Telegram Bot API.</p>
                    <label>
                        Bot Token
                        <input
                            type="password"
                            placeholder="123456789:ABCdefGHIjklMNO..."
                            value={telegramToken}
                            onChange={(e) => setTelegramToken(e.target.value)}
                        />
                    </label>
                    <button onClick={() => handleSave("Telegram")}>Connect Telegram</button>
                </div>

                {/* Discord Card */}
                <div className="setup-card">
                    <div className="card-icon discord-icon">🎮</div>
                    <h3>Discord</h3>
                    <p>Connect via Discord Developer Portal.</p>
                    <label>
                        Bot Token
                        <input
                            type="password"
                            placeholder="MTAxMjM0NTY3ODkw..."
                            value={discordToken}
                            onChange={(e) => setDiscordToken(e.target.value)}
                        />
                    </label>
                    <button onClick={() => handleSave("Discord")}>Connect Discord</button>
                </div>

                {/* Signal Card */}
                <div className="setup-card">
                    <div className="card-icon signal-icon">💬</div>
                    <h3>Signal</h3>
                    <p>Requires a self-hosted signal-cli REST bridge.</p>
                    <label>
                        Bridge URL
                        <input
                            type="text"
                            placeholder="http://localhost:8080"
                            value={signalUrl}
                            onChange={(e) => setSignalUrl(e.target.value)}
                        />
                    </label>
                    <button onClick={() => handleSave("Signal")}>Connect Signal</button>
                </div>

                {/* iMessage Card */}
                <div className="setup-card">
                    <div className="card-icon imessage-icon">🍏</div>
                    <h3>iMessage</h3>
                    <p>Requires BlueBubbles or a macOS AppleScript bridge.</p>
                    <label>
                        Bridge Host URL
                        <input
                            type="text"
                            placeholder="http://mac-mini.local:1234"
                            value={iMessageUrl}
                            onChange={(e) => setIMessageUrl(e.target.value)}
                        />
                    </label>
                    <button onClick={() => handleSave("iMessage")}>Connect iMessage</button>
                </div>
            </div>
        </div>
    );
}
