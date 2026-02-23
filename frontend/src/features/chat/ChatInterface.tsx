import { useState, useRef, useEffect, useMemo } from "react";
import { getRuntimeConfig, apiRequest } from "../../lib/api";

interface Message {
    id?: string;
    role: "user" | "assistant" | "system";
    content: string;
    translation?: string;
    isTranslating?: boolean;
}

// Browser API fallbacks
const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

interface ChatInterfaceProps {
    token: string;
    apiKey: string;
}

export function ChatInterface({ token, apiKey }: ChatInterfaceProps): JSX.Element {
    const [messages, setMessages] = useState<Message[]>([
        { role: "system", content: "You are a helpful AI assistant." },
        { role: "assistant", content: "Hello! I am AGENT-33. How can I assist you today?" }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    // Voice Generation (TTS) State
    const [voiceEnabled, setVoiceEnabled] = useState(false);
    const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
    const [selectedVoiceURI, setSelectedVoiceURI] = useState<string>("");
    const [playbackRate, setPlaybackRate] = useState<number>(1.0);
    const [lastSpokenText, setLastSpokenText] = useState<string>("");

    // Translation State
    const [translationEnabled, setTranslationEnabled] = useState(false);
    const [translateFrom, setTranslateFrom] = useState("English");
    const [translateTo, setTranslateTo] = useState("Spanish");

    // Settings Modal State
    const [showSettingsModal, setShowSettingsModal] = useState(false);
    const [activeSettingsTab, setActiveSettingsTab] = useState<'translation' | 'audio'>('translation');

    // Voice Dictation (STT) State
    const [isRecording, setIsRecording] = useState(false);
    const recognitionRef = useRef<any>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { API_BASE_URL } = getRuntimeConfig();

    // Initialize Voices
    useEffect(() => {
        const loadVoices = () => {
            const voices = window.speechSynthesis.getVoices();
            setAvailableVoices(voices);
            if (voices.length > 0 && !selectedVoiceURI) {
                // Try to find a default English voice
                const defaultVoice = voices.find(v => v.lang.startsWith("en-") && v.default) || voices.find(v => v.lang.startsWith("en-")) || voices[0];
                setSelectedVoiceURI(defaultVoice.voiceURI);
            }
        };

        // Chrome requires this event, Safari/Firefox might load immediately
        window.speechSynthesis.onvoiceschanged = loadVoices;
        loadVoices();

        return () => {
            window.speechSynthesis.cancel(); // Stop playing on unmount
        };
    }, []);

    // Initialize Speech Recognition
    useEffect(() => {
        if (SpeechRecognitionAPI) {
            const recognition = new SpeechRecognitionAPI();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onresult = (event: any) => {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                if (finalTranscript) {
                    setInput((prev) => prev + (prev.endsWith(" ") ? "" : " ") + finalTranscript);
                }
            };

            recognition.onerror = (event: any) => {
                console.error("Speech recognition error", event.error);
                setIsRecording(false);
            };

            recognition.onend = () => {
                setIsRecording(false);
            };

            recognitionRef.current = recognition;
        }
    }, []);

    const toggleRecording = () => {
        if (isRecording) {
            recognitionRef.current?.stop();
            setIsRecording(false);
        } else {
            if (recognitionRef.current) {
                recognitionRef.current.start();
                setIsRecording(true);
            } else {
                alert("Speech recognition is not supported in this browser.");
            }
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const speakText = (text: string) => {
        if (!voiceEnabled || !window.speechSynthesis) return;

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        setLastSpokenText(text);

        const utterance = new SpeechSynthesisUtterance(text);
        const selectedVoice = availableVoices.find(v => v.voiceURI === selectedVoiceURI);

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        utterance.rate = playbackRate;
        window.speechSynthesis.speak(utterance);
    };

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        // Stop recording if speaking
        if (isRecording) {
            recognitionRef.current?.stop();
            setIsRecording(false);
        }

        const userMsg: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const res = await apiRequest({
                method: "POST",
                path: "/v1/chat/completions",
                token: token,
                apiKey: apiKey,
                body: JSON.stringify({
                    model: "qwen3-coder:30b", // Default fallback model
                    messages: [...messages, userMsg],
                    temperature: 0.2
                })
            });

            if (!res.ok) {
                if (res.status === 401) {
                    throw new Error("Unauthorized (401): Your API token has expired or is invalid. Please go to the Integrations tab and click 'Sign In' to refresh it.");
                }
                throw new Error(`API Error: ${res.status}`);
            }

            // res.data will be the parsed JSON object
            const data = res.data as any;
            const reply = data.choices?.[0]?.message?.content || "No response received.";
            const msgId = Date.now().toString() + Math.random().toString();
            const newMsg: Message = { id: msgId, role: "assistant", content: reply, isTranslating: translationEnabled };

            setMessages((prev) => [...prev, newMsg]);

            if (translationEnabled) {
                // Fire off translation in the background
                (async () => {
                    try {
                        const transRes = await apiRequest({
                            method: "POST",
                            path: "/v1/chat/completions",
                            token: token,
                            apiKey: apiKey,
                            body: JSON.stringify({
                                model: "qwen3-coder:30b",
                                messages: [
                                    { role: "system", content: `You are a professional translator. Translate the following text from ${translateFrom} to ${translateTo}. Return ONLY the direct translation, nothing else, no quotes, no markdown.` },
                                    { role: "user", content: reply }
                                ],
                                temperature: 0.1
                            })
                        });

                        if (transRes.ok) {
                            const tData = transRes.data as any;
                            const tReply = tData.choices?.[0]?.message?.content || "Translation failed.";
                            setMessages(prev => prev.map(m => m.id === msgId ? { ...m, translation: tReply, isTranslating: false } : m));
                        } else {
                            throw new Error("Translation request failed");
                        }
                    } catch (e: any) {
                        console.error("Auto-translation error:", e);
                        setMessages(prev => prev.map(m => m.id === msgId ? { ...m, translation: `[Error: ${e.message}]`, isTranslating: false } : m));
                    }
                })();
            }

            // Auto-speak the response if enabled
            speakText(reply);

        } catch (err: any) {
            console.error(err);
            setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err.message}` }]);
        } finally {
            setLoading(false);
        }
    };

    const handleTranslate = async (index: number) => {
        const msgToTranslate = messages[index];
        if (!msgToTranslate || !msgToTranslate.content) return;

        setMessages(prev => prev.map((m, i) => i === index ? { ...m, isTranslating: true } : m));

        try {
            const res = await apiRequest({
                method: "POST",
                path: "/v1/chat/completions",
                token: token,
                apiKey: apiKey,
                body: JSON.stringify({
                    model: "qwen3-coder:30b",
                    messages: [
                        { role: "system", content: `You are a professional translator. Translate the following text from ${translateFrom} to ${translateTo}. Return ONLY the direct translation, nothing else, no quotes, no markdown.` },
                        { role: "user", content: msgToTranslate.content }
                    ],
                    temperature: 0.1
                })
            });

            if (!res.ok) {
                if (res.status === 401) {
                    throw new Error("Unauthorized (401). Please sign in on the Integrations tab.");
                }
                throw new Error(`API Error: ${res.status}`);
            }

            const data = res.data as any;
            const translation = data.choices?.[0]?.message?.content || "Translation failed.";

            setMessages(prev => prev.map((m, i) => i === index ? { ...m, translation, isTranslating: false } : m));

        } catch (err: any) {
            console.error("Translation error:", err);
            setMessages(prev => prev.map((m, i) => i === index ? { ...m, translation: `[Error: ${err.message}]`, isTranslating: false } : m));
        }
    };

    // Retroactively translate the last 3 assistant messages when toggled ON
    useEffect(() => {
        if (translationEnabled && messages.length > 0) {
            // Find the indices of the last 3 assistant messages that don't have a translation yet
            const indicesToTranslate: number[] = [];
            for (let i = messages.length - 1; i >= 0 && indicesToTranslate.length < 3; i--) {
                const msg = messages[i];
                if (msg.role === "assistant" && !msg.translation && !msg.isTranslating) {
                    indicesToTranslate.push(i);
                }
            }
            // Fire off translations for those specific indices
            indicesToTranslate.forEach(index => handleTranslate(index));
        }
    }, [translationEnabled, translateFrom, translateTo]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-interface">
            <div className="chat-messages">
                {messages.map((msg, index) => {
                    if (msg.role === "system") return null;
                    return (
                        <div key={index} className={`chat-bubble-container ${msg.role}`}>
                            {msg.role === "user" && (
                                <div className="chat-bubble-actions">
                                    <button
                                        className="inline-action-btn"
                                        onClick={() => handleTranslate(index)}
                                        title={`Translate from ${translateFrom} to ${translateTo}`}
                                        disabled={msg.isTranslating}
                                    >
                                        🌐
                                    </button>
                                </div>
                            )}
                            <div className={`chat-bubble ${msg.role}`}>
                                {msg.content}
                                {msg.translation && (
                                    <div className="chat-translation">
                                        <hr />
                                        <i>{msg.translation}</i>
                                    </div>
                                )}
                                {msg.isTranslating && (
                                    <div className="chat-translation translating">
                                        <hr />
                                        <i>Translating {translateFrom} to {translateTo}...</i>
                                    </div>
                                )}
                            </div>
                            {msg.role === "assistant" && (
                                <div className="chat-bubble-actions">
                                    {voiceEnabled && (
                                        <button
                                            className="inline-action-btn"
                                            onClick={() => speakText(msg.content)}
                                            title="Read aloud"
                                        >
                                            🔊
                                        </button>
                                    )}
                                    <button
                                        className="inline-action-btn"
                                        onClick={() => handleTranslate(index)}
                                        title={`Translate from ${translateFrom} to ${translateTo}`}
                                        disabled={msg.isTranslating}
                                    >
                                        🌐
                                    </button>
                                </div>
                            )}
                        </div>
                    );
                })}
                {loading && (
                    <div className="chat-bubble-container assistant">
                        <div className="chat-bubble assistant typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                <button
                    className={`mic-btn ${isRecording ? "recording" : ""}`}
                    onClick={toggleRecording}
                    title={isRecording ? "Stop dictation" : "Start dictation"}
                >
                    🎤
                </button>
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message AGENT-33 (or click the mic to speak)..."
                    rows={1}
                    disabled={loading}
                />
                <button onClick={handleSend} disabled={(!input.trim() && !isRecording) || loading} className="chat-send-bin" title="Send (Enter)">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                        <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                    </svg>
                </button>
                <button
                    className="settings-gear-btn"
                    onClick={() => setShowSettingsModal(prev => !prev)}
                    title="Chat Settings"
                >
                    ⚙️
                </button>

                {showSettingsModal && (
                    <div className="settings-popover">
                        <div className="settings-popover-header">
                            <h2>Chat Settings</h2>
                            <button className="settings-close-btn" onClick={() => setShowSettingsModal(false)}>✕</button>
                        </div>

                        <div className="chat-tab-group compact">
                            <button
                                className={`chat-tab-btn ${activeSettingsTab === 'translation' ? "active" : ""}`}
                                onClick={() => setActiveSettingsTab('translation')}
                            >
                                Translation Options
                            </button>
                            <button
                                className={`chat-tab-btn ${activeSettingsTab === 'audio' ? "active" : ""}`}
                                onClick={() => setActiveSettingsTab('audio')}
                            >
                                Audio Response
                            </button>
                        </div>

                        <div className="chat-tab-panel compact">
                            {activeSettingsTab === 'translation' && (
                                <div className="translation-lang-selects">
                                    <div className="setting-row">
                                        <span className="setting-label">Auto-Translate</span>
                                        <label className="voice-toggle">
                                            <input
                                                type="checkbox"
                                                checked={translationEnabled}
                                                onChange={(e) => setTranslationEnabled(e.target.checked)}
                                            />
                                            <span className="slider"></span>
                                        </label>
                                    </div>

                                    <span>From:</span>
                                    <select className="voice-select inline" value={translateFrom} onChange={(e) => setTranslateFrom(e.target.value)}>
                                        <option value="English">English</option>
                                        <option value="Spanish">Spanish</option>
                                        <option value="French">French</option>
                                        <option value="German">German</option>
                                        <option value="Italian">Italian</option>
                                        <option value="Japanese">Japanese</option>
                                        <option value="Chinese">Chinese</option>
                                        <option value="Russian">Russian</option>
                                        <option value="Arabic">Arabic</option>
                                        <option value="Korean">Korean</option>
                                        <option value="Portuguese">Portuguese</option>
                                    </select>

                                    <span>To:</span>
                                    <select className="voice-select inline" value={translateTo} onChange={(e) => setTranslateTo(e.target.value)}>
                                        <option value="English">English</option>
                                        <option value="Spanish">Spanish</option>
                                        <option value="French">French</option>
                                        <option value="German">German</option>
                                        <option value="Italian">Italian</option>
                                        <option value="Japanese">Japanese</option>
                                        <option value="Chinese">Chinese</option>
                                        <option value="Russian">Russian</option>
                                        <option value="Arabic">Arabic</option>
                                        <option value="Korean">Korean</option>
                                        <option value="Portuguese">Portuguese</option>
                                    </select>
                                </div>
                            )}

                            {activeSettingsTab === 'audio' && (
                                <div className="audio-panel-grid">
                                    <div className="setting-row">
                                        <span className="setting-label">Enable TTS (Read Aloud)</span>
                                        <label className="voice-toggle">
                                            <input
                                                type="checkbox"
                                                checked={voiceEnabled}
                                                onChange={(e) => {
                                                    setVoiceEnabled(e.target.checked);
                                                    if (!e.target.checked) window.speechSynthesis.cancel();
                                                }}
                                            />
                                            <span className="slider"></span>
                                        </label>
                                    </div>

                                    {voiceEnabled && (
                                        <div className="audio-actions-row">
                                            <select
                                                className="voice-select"
                                                value={selectedVoiceURI}
                                                onChange={(e) => setSelectedVoiceURI(e.target.value)}
                                            >
                                                {availableVoices.map(voice => (
                                                    <option key={voice.voiceURI} value={voice.voiceURI}>
                                                        {voice.name} ({voice.lang})
                                                    </option>
                                                ))}
                                            </select>

                                            <select
                                                className="voice-select voice-speed inline"
                                                value={playbackRate}
                                                onChange={(e) => {
                                                    const newRate = parseFloat(e.target.value);
                                                    setPlaybackRate(newRate);
                                                    if (window.speechSynthesis.speaking && lastSpokenText) {
                                                        window.speechSynthesis.cancel();
                                                        setTimeout(() => {
                                                            const utterance = new SpeechSynthesisUtterance(lastSpokenText);
                                                            const selectedVoice = availableVoices.find(v => v.voiceURI === selectedVoiceURI);
                                                            if (selectedVoice) {
                                                                utterance.voice = selectedVoice;
                                                            }
                                                            utterance.rate = newRate;
                                                            window.speechSynthesis.speak(utterance);
                                                        }, 50);
                                                    }
                                                }}
                                            >
                                                <option value={0.8}>0.8x</option>
                                                <option value={1.0}>1x</option>
                                                <option value={1.2}>1.2x</option>
                                                <option value={1.5}>1.5x</option>
                                                <option value={2.0}>2x</option>
                                                <option value={2.5}>2.5x</option>
                                                <option value={3.0}>3x</option>
                                            </select>

                                            <button
                                                className="replay-audio-btn"
                                                onClick={() => lastSpokenText && speakText(lastSpokenText)}
                                                title="Replay last audio message"
                                                disabled={!lastSpokenText}
                                            >
                                                🔄
                                            </button>

                                            <button
                                                className="stop-audio-btn"
                                                onClick={() => window.speechSynthesis.cancel()}
                                                title="Stop playing audio"
                                            >
                                                ⏹️
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
