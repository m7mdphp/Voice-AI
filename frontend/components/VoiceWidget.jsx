import React, { useState, useEffect, useRef } from 'react';

const VoiceWidget = ({ tenantId, userId }) => {
    // States: idle, listening, thinking, speaking
    const [uiState, setUiState] = useState('idle');
    const [messages, setMessages] = useState([]);

    const ws = useRef(null);
    const audioCtx = useRef(null);
    const audioQueue = useRef([]);
    const isPlaying = useRef(false);
    const processor = useRef(null);
    const mediaStream = useRef(null);

    useEffect(() => {
        connect();
        return () => cleanup();
    }, []);

    const connect = () => {
        ws.current = new WebSocket(`ws://localhost:8000/ws/session/${tenantId}/${userId}`);

        ws.current.onopen = () => console.log('Connected');

        ws.current.onmessage = async (e) => {
            if (typeof e.data !== 'string') {
                // Binary Audio
                const chunk = await e.data.arrayBuffer();
                audioQueue.current.push(chunk);
                if (!isPlaying.current) playQueue();
            } else {
                // JSON Control
                const msg = JSON.parse(e.data);
                if (msg.type === 'state') {
                    setUiState(msg.state);
                } else if (msg.type === 'audio_start') {
                    // Backend explicitly says audio is coming
                } else if (msg.type === 'audio_end') {
                    // Backend finished sending. Frontend finishes playing queue then resets.
                } else if (msg.type === 'text') {
                    setMessages(p => [...p, { role: 'ai', text: msg.content }]);
                }
            }
        };
    };

    const playQueue = async () => {
        if (audioQueue.current.length === 0) {
            isPlaying.current = false;
            // If server sent "audio_end", and queue empty, we can revert to listening locally if needed
            // But we rely on server "state" message usually.
            return;
        }

        isPlaying.current = true;
        const chunk = audioQueue.current.shift();

        if (!audioCtx.current) audioCtx.current = new (window.AudioContext || window.webkitAudioContext)();

        try {
            const buffer = await audioCtx.current.decodeAudioData(chunk);
            const source = audioCtx.current.createBufferSource();
            source.buffer = buffer;
            source.connect(audioCtx.current.destination);
            source.onended = playQueue;
            source.start(0);
        } catch (err) {
            console.error("Decode error", err);
            playQueue();
        }
    };

    const startMic = async () => {
        try {
            if (!audioCtx.current) audioCtx.current = new (window.AudioContext || window.webkitAudioContext)();
            await audioCtx.current.resume();

            mediaStream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
            const source = audioCtx.current.createMediaStreamSource(mediaStream.current);
            processor.current = audioCtx.current.createScriptProcessor(4096, 1, 1);

            source.connect(processor.current);
            processor.current.connect(audioCtx.current.destination);

            processor.current.onaudioprocess = (e) => {
                // CRITICAL: WALKIE TALKIE LOGIC
                // Only send if state is 'listening'. Block if 'thinking' or 'speaking'.
                if (uiState !== 'listening') return;

                if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                    const inputData = e.inputBuffer.getChannelData(0);
                    // Float32 -> Int16 conversion recommended here for bandwidth, 
                    // but sending float buffer works for local MVP
                    ws.current.send(inputData);
                }
            };

            setUiState('listening');

        } catch (e) {
            console.error("Mic Error", e);
        }
    };

    const cleanup = () => {
        if (ws.current) ws.current.close();
        if (audioCtx.current) audioCtx.current.close();
    };

    return (
        <div className="p-6 bg-gray-50 max-w-md mx-auto rounded-xl shadow-lg mt-10 text-center">
            <h1 className="text-2xl font-bold mb-4 text-blue-800">Tiryaq Medic AI</h1>

            <div className={`w-40 h-40 mx-auto rounded-full flex items-center justify-center text-4xl shadow-inner mb-6 transition-colors duration-300
        ${uiState === 'listening' ? 'bg-green-500 animate-pulse' :
                    uiState === 'thinking' ? 'bg-yellow-400 animate-spin' :
                        uiState === 'speaking' ? 'bg-red-500 animate-bounce' : 'bg-gray-300'
                }`}>
                {uiState === 'listening' ? '🎙️' :
                    uiState === 'thinking' ? '⚙️' :
                        uiState === 'speaking' ? '🔊' : '🛑'}
            </div>

            <div className="font-bold text-gray-700 mb-4 uppercase tracking-widest">
                {uiState}
            </div>

            <div className="h-40 overflow-y-auto bg-white border p-2 rounded text-left text-sm">
                {messages.map((m, i) => (
                    <div key={i} className="mb-1 border-b pb-1">
                        <span className="font-bold text-blue-600">AI: </span>{m.text}
                    </div>
                ))}
            </div>

            <div className="mt-4">
                {uiState === 'idle' && (
                    <button onClick={startMic} className="bg-blue-600 text-white px-8 py-3 rounded-full font-bold shadow-lg transform active:scale-95 transition-transform">
                        START CONSULTATION
                    </button>
                )}
            </div>
        </div>
    );
};

export default VoiceWidget;
