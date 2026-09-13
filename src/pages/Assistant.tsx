import React, { useState } from 'react';
import GlassCard from '../components/GlassCard';
import { sendChatMessage } from '../lib/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: any[];
  suggestedActions?: string[];
  timestamp: string;
}

interface Props {
  selectedProjectId?: string;
  onNavigateToProject?: (projectId: string) => void;
}

export default function Assistant({ selectedProjectId = 'P1024' }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'assistant',
      text: `Welcome to PAIMANA Intelligence Assistant. Connected to your FastAPI intelligence backend and MongoDB cluster. I can analyze risk scores, explain SHAP drivers for projects like ${selectedProjectId}, detect velocity stagnation, and recommend interventions. How can I assist you?`,
      citations: [
        { feature: 'Live Database', impact: '1,500 Projects', description: 'MongoDB paimana_intelligence connected' },
        { feature: 'SHAP TreeExplainer', impact: 'Real-time', description: 'XGBoost feature attributions available' },
      ],
      suggestedActions: [
        `Why is ${selectedProjectId} high?`,
        'Which projects are elevated?',
        `Recommend actions for ${selectedProjectId}`,
        `What is the trend for ${selectedProjectId}?`
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(text, selectedProjectId);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.reply || 'No response from intelligence engine.',
        citations: response.grounded_evidence || [],
        suggestedActions: response.suggested_actions || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: 'Error contacting backend service. Please check that FastAPI is running on port 8000.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-20 sm:pt-24 pb-6 px-4 sm:px-8 md:px-12 max-w-5xl mx-auto flex flex-col h-[calc(100vh-80px)] justify-between space-y-3 sm:space-y-4">
      {/* Header */}
      <GlassCard variant="hero" padding={18} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-bold font-display text-white">
            PAIMANA Intelligence Assistant
          </h2>
          <p className="text-xs sm:text-sm text-white/70">
            Executive decision-support chat grounded in FastAPI tools, MongoDB time-series & SHAP
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono-code px-3 py-1 rounded-full bg-white/10 text-white font-semibold border border-white/20 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            <span>FastAPI: 8000</span>
          </span>
        </div>
      </GlassCard>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 sm:space-y-4 pr-1 sm:pr-2">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[94%] sm:max-w-[85%] rounded-2xl p-4 sm:p-5 text-xs sm:text-sm md:text-base space-y-3 shadow-lg ${
                msg.sender === 'user'
                  ? 'bg-white text-black font-semibold'
                  : 'oled-solid-card text-white border border-white/20'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed font-sans">{msg.text}</div>

              {/* Citations & Evidence Footprints */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-3 border-t border-white/10 space-y-2">
                  <div className="text-[11px] sm:text-xs font-mono-code uppercase font-bold text-white/60">
                    Evidence Footprints:
                  </div>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {msg.citations.map((c, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded bg-white/10 border border-white/20 text-[11px] sm:text-xs font-mono-code text-white"
                      >
                        {c.feature}: {c.impact} pts
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Follow-up Actions */}
              {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                <div className="pt-3 border-t border-white/10 flex flex-wrap gap-1.5 sm:gap-2">
                  {msg.suggestedActions.map((action, ai) => (
                    <button
                      key={ai}
                      onClick={() => handleSend(action)}
                      className="px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg bg-white/10 hover:bg-white hover:text-black border border-white/20 text-[11px] sm:text-xs md:text-sm font-mono-code text-white transition-all cursor-pointer font-medium"
                    >
                      → {action}
                    </button>
                  ))}
                </div>
              )}

              <div className="text-[10px] sm:text-xs text-right opacity-60 font-mono-code">{msg.timestamp}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs sm:text-sm text-white/70 font-mono-code p-2">
            <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
            <span>Consulting intelligence pipeline tools...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <GlassCard variant="medium" padding={12} className="flex items-center gap-2 sm:gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder={`Ask about ${selectedProjectId} delays, SHAP, recommendations...`}
          className="flex-1 bg-transparent border-none text-xs sm:text-sm md:text-base text-white outline-none px-2 sm:px-3 font-sans placeholder:text-white/40"
        />

        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl bg-white text-black hover:bg-zinc-200 text-xs sm:text-sm font-mono-code font-bold cursor-pointer transition-all shadow-md disabled:opacity-40 shrink-0"
        >
          Send
        </button>
      </GlassCard>
    </div>
  );
}
