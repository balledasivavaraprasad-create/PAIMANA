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
      text: `Welcome to PAIMANA Intelligence Assistant. I am connected directly to your FastAPI intelligence backend and MongoDB cluster. I can analyze risk scores, explain SHAP drivers for projects like ${selectedProjectId}, detect velocity stagnation, and recommend interventions. How can I assist you?`,
      citations: [
        { feature: 'Live Database', impact: '1,500 Projects', description: 'MongoDB paimana_intelligence connected' },
        { feature: 'SHAP TreeExplainer', impact: 'Real-time', description: 'XGBoost feature attributions available' },
      ],
      suggestedActions: [
        `Why is ${selectedProjectId} critical?`,
        'Which projects are critical?',
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
    <div className="pt-20 pb-8 px-6 md:px-16 max-w-5xl mx-auto flex flex-col h-[calc(100vh-30px)] justify-between space-y-4">
      {/* Header */}
      <GlassCard variant="hero" padding={20} className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold font-display text-[var(--text-primary)]">
            PAIMANA Intelligence Assistant
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Executive decision-support chat grounded in FastAPI tools, MongoDB time-series & SHAP
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono-code px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Connected to http://localhost:8000</span>
          </span>
        </div>
      </GlassCard>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 text-xs space-y-2.5 shadow-lg ${
                msg.sender === 'user'
                  ? 'bg-[var(--accent)] text-white'
                  : 'oled-solid-card text-[var(--text-primary)] border border-white/20'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed font-sans">{msg.text}</div>

              {/* Citations & Evidence Footprints */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-2 border-t border-[var(--border-hairline)] space-y-1">
                  <div className="text-[9px] font-mono-code uppercase font-bold text-[var(--text-muted)]">
                    Evidence Footprints:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {msg.citations.map((c, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[10px] font-mono-code text-[var(--accent)]"
                      >
                        {c.feature}: {c.impact} pts
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Follow-up Actions */}
              {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                <div className="pt-2 border-t border-[var(--border-hairline)] flex flex-wrap gap-1.5">
                  {msg.suggestedActions.map((action, ai) => (
                    <button
                      key={ai}
                      onClick={() => handleSend(action)}
                      className="px-2.5 py-1 rounded-lg bg-[var(--surface-sunken)] hover:bg-[var(--accent-soft)] border border-[var(--border-hairline)] text-[10px] font-mono-code text-[var(--text-secondary)] hover:text-[var(--accent)] transition-all cursor-pointer"
                    >
                      → {action}
                    </button>
                  ))}
                </div>
              )}

              <div className="text-[9px] text-right opacity-60 font-mono-code">{msg.timestamp}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] font-mono-code p-2">
            <span className="w-3 h-3 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
            <span>Consulting intelligence pipeline tools...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <GlassCard variant="medium" padding={12} className="flex items-center gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder={`Ask about delays, SHAP risk factors, or recommendations for ${selectedProjectId}...`}
          className="flex-1 bg-transparent border-none text-xs text-[var(--text-primary)] outline-none px-2 font-sans placeholder:text-[var(--text-muted)]"
        />

        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="px-4 py-2 rounded-xl bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-xs font-mono-code font-bold cursor-pointer transition-all shadow-md disabled:opacity-50"
        >
          Send
        </button>
      </GlassCard>
    </div>
  );
}
