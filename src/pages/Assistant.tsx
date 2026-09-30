import React, { useState } from 'react';
import GlassCard from '../components/GlassCard';
import FormattedMessage from '../components/FormattedMessage';
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
  allProjects?: any[];
  onNavigateToProject?: (projectId: string) => void;
}

export default function Assistant({ selectedProjectId, currentUser, allProjects, onNavigateToProject }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  const officerName = currentUser?.full_name || (isAdmin ? 'National Director' : 'Project Officer');
  const ministryName = currentUser?.ministry || (isAdmin ? 'MoSPI Infrastructure Coordination' : 'Ministry of Housing & Urban Affairs');

  const initialGreeting = isAdmin
    ? `Welcome ${officerName}. I am your PAIMANA Intelligence Assistant. I have live access to your infrastructure project database across all monitored corridors. Ask me about critical delay clusters, project status, schedule slippages, or query any specific project.`
    : `Hello ${officerName}! I am your PAIMANA Intelligence Assistant. I am connected to your live infrastructure database under ${ministryName}. Ask me about any of your projects, schedule delays, recent changes, or upcoming milestones.`;

  const initialSuggested = isAdmin
    ? [
        'Which projects face the highest delay risk?',
        'What are the recent schedule slippage changes?',
        'Show all monitored projects',
        'Tell me about the highest risk project'
      ]
    : [
        'Show my assigned projects',
        'What are the recent delay changes?',
        'Which of my projects need immediate attention?',
        'Tell me about my highest risk project'
      ];

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'assistant',
      text: initialGreeting,
      citations: [
        { feature: 'Assistant', impact: 'Interactive Intelligence' },
        { feature: 'Database', impact: 'Live Atlas DB Synchronized' },
      ],
      suggestedActions: initialSuggested,
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

    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const history = updatedMessages.slice(-6).map(m => ({ sender: m.sender, text: m.text }));
      const response = await sendChatMessage(
        text,
        selectedProjectId,
        currentUser?.role || 'PROJECT_OFFICER',
        currentUser?.username,
        currentUser?.ministry,
        history,
        allProjects
      );

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.reply || 'No response received from the intelligence engine.',
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
          text: 'Hello! My name is PAIMANA Intelligence. How can I help you today?',
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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl sm:text-2xl font-bold font-display tracking-tight text-white">
              PAIMANA Intelligence Assistant
            </h2>
            <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${
              isAdmin ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            }`}>
              {isAdmin ? 'Admin National Mode' : 'Officer Portfolio Mode'}
            </span>
          </div>
          <span className="text-xs font-mono text-white/60">
            {currentUser?.username || 'officer'}
          </span>
        </div>
        <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-700'}`}>
          {isAdmin
            ? 'Interactive national infrastructure assistant. Query systemic delays, inter-ministerial benchmarks, and cross-state risks.'
            : 'Interactive department assistant. Ask questions about your assigned projects, milestone delays, and ground recovery steps.'}
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
                  ? (isDark ? 'bg-white text-black font-semibold' : 'bg-black text-white font-semibold user-bubble-light')
                  : (isDark ? 'oled-solid-card text-white border border-white/20' : 'oled-solid-card text-slate-900 border border-slate-300')
              }`}
              style={msg.sender === 'user' && !isDark ? { color: '#ffffff' } : undefined}
            >
              <FormattedMessage
                text={msg.text}
                isDark={isDark}
                isUser={msg.sender === 'user'}
                onNavigateToProject={onNavigateToProject}
              />

              {/* Citations & Evidence Footprints */}
              {msg.citations && msg.citations.length > 0 && (
                <div className={`pt-3 border-t space-y-2 ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
                  <div className={`text-[11px] sm:text-xs font-mono-code uppercase font-bold ${isDark ? 'text-white/60' : 'text-slate-600'}`}>
                    Evidence &amp; Verified Telemetry:
                  </div>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {msg.citations.map((c, idx) => (
                      <span
                        key={idx}
                        className={`px-2.5 py-1 rounded text-[11px] sm:text-xs font-mono-code border ${
                          isDark ? 'bg-white/10 border-white/20 text-white' : 'bg-slate-100 border-slate-300 text-slate-800'
                        }`}
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
            <span>Analyzing project portfolio and generating response...</span>
          </div>
        )}
      </div>

      {/* Interactive Prompt Bar */}
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
            placeholder={isAdmin ? "Ask about national projects, systemic delays, or compare ministries..." : "Ask about your projects, milestone delays, or request a summary..."}
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
