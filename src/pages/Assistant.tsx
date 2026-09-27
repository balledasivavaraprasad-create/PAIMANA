import React, { useState } from 'react';
import GlassCard from '../components/GlassCard';
import { sendChatMessage, UserProfile } from '../lib/api';
import { useTheme } from '../hooks/useTheme';

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
  currentUser?: UserProfile | null;
  onNavigateToProject?: (projectId: string) => void;
}

export default function Assistant({ selectedProjectId = 'P1024', currentUser }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const officerName = currentUser?.full_name || 'Officer';
  const ministryName = currentUser?.ministry || 'Infrastructure Administration';

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'assistant',
      text: `Hello ${officerName}! I am your InfraBuild AI project assistant. I am connected to your projects in ${ministryName}. How can I help you check project delays, budget spending, or upcoming deadlines today?`,
      citations: [
        { feature: 'Department', impact: ministryName, description: 'Focused on your department' },
        { feature: 'Active Projects', impact: 'Monitored', description: 'Live tracking active' },
        { feature: 'Risk Engine', impact: 'Ready', description: 'Delay and cost calculations ready' },
      ],
      suggestedActions: [
        'Which of my projects need attention?',
        `Why is this project at risk?`,
        'What caused the delay?',
        'What should we do to recover lost time?',
        'Which milestone is at risk?',
        'Which projects have increasing risk?'
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
          text: 'Error contacting backend service. Please check that the server is running.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-16 sm:pt-20 pb-6 px-4 sm:px-8 md:px-12 max-w-5xl mx-auto flex flex-col h-[calc(100vh-65px)] justify-between space-y-3 sm:space-y-4">
      {/* Header */}
      <GlassCard variant="hero" padding={20} className="w-full space-y-1.5">
        <h2 className="text-xl sm:text-2xl font-bold font-display tracking-tight">
          InfraBuild AI Assistant
        </h2>
        <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-700'}`}>
          Ask any question about your projects, costs, milestone delays, and get clear, instant answers backed by project data.
        </p>
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
                  ? (isDark ? 'bg-white text-black font-semibold' : 'bg-black text-white font-semibold')
                  : 'oled-solid-card text-white border border-white/20'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed font-sans">{msg.text}</div>

              {/* Citations & Evidence Footprints */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-3 border-t border-white/10 space-y-2">
                  <div className={`text-[11px] sm:text-xs font-mono-code uppercase font-bold ${isDark ? 'text-white/60' : 'text-slate-600'}`}>
                    Evidence &amp; Verified Facts:
                  </div>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {msg.citations.map((c, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded bg-white/10 border border-white/20 text-[11px] sm:text-xs font-mono-code"
                      >
                        {c.feature}: {c.impact}
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
                      className={`px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg border text-[11px] sm:text-xs md:text-sm font-mono-code transition-all cursor-pointer font-medium ${
                        isDark
                          ? 'bg-white/10 hover:bg-white hover:text-black border-white/20 text-white'
                          : 'bg-black/5 hover:bg-black hover:text-white border-black/15 text-black'
                      }`}
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
          <div className={`flex items-center gap-2 text-xs sm:text-sm font-mono-code p-2 ${
            isDark ? 'text-white/70' : 'text-slate-600'
          }`}>
            <span className={`w-3.5 h-3.5 rounded-full border-2 border-t-transparent animate-spin ${
              isDark ? 'border-white' : 'border-black'
            }`} />
            <span>Checking project updates and records...</span>
          </div>
        )}
      </div>

      {/* Seamless Prompt Flashcard */}
      <div className={`p-2.5 sm:p-3 rounded-2xl border backdrop-blur-xl transition-all duration-200 shadow-xl ${
        isDark
          ? 'bg-[#0B0F17]/90 border-white/20 shadow-[0_8px_32px_rgba(0,0,0,0.6)] focus-within:border-white/40'
          : 'bg-white/95 border-slate-300 shadow-[0_4px_24px_rgba(0,0,0,0.08)] focus-within:border-black/40'
      }`}>
        <div className="flex items-center gap-2 sm:gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about your project, budget, or delays..."
            className={`flex-1 bg-transparent border-none text-xs sm:text-sm md:text-base outline-none px-3 py-1.5 font-sans ${
              isDark
                ? 'text-white placeholder:text-white/40'
                : 'text-slate-900 placeholder:text-slate-400'
            }`}
          />

          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className={`px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 flex items-center gap-2 cursor-pointer shadow-md disabled:opacity-40 shrink-0 ${
              isDark
                ? 'bg-white text-black hover:bg-slate-200'
                : 'bg-black text-white hover:bg-zinc-800'
            }`}
          >
            <span>Send</span>
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
