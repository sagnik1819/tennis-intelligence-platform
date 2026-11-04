import React, { useState } from 'react';
import { Bot, Send, Sparkles, User, Database, ArrowRight, ShieldCheck } from 'lucide-react';
import { TennisAPI } from '../services/api';

const STARTER_PROMPTS = [
  "Who are the top 5 ranked available players?",
  "Compare Mate Pavic and Jordan Thompson",
  "Which countries have the most competitors?",
  "Show available competitions and tournaments"
];

export default function AIAssistantPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your AI Tennis Sports Intelligence Analyst. I can answer queries regarding official circuit rankings, compare competitors side-by-side, analyze national player densities, and explain ML trait vectors. Every answer is grounded directly in certified database records.',
      citations: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await TennisAPI.askAssistant(query);
      const assistantMsg = {
        role: 'assistant',
        content: res.response,
        citations: res.citations || [],
        suggested_actions: res.suggested_actions || []
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an issue querying the database tools. Please try again.',
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col space-y-4">
      {/* HEADER */}
      <div className="flex items-center justify-between border-b border-slateBorder/60 pb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-tennis-green/10 border border-tennis-green/30 flex items-center justify-center text-tennis-green">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-heading font-extrabold text-white">AI Tennis Intelligence Assistant</h1>
            <p className="text-xs text-textSecondary flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-tennis-green" /> 100% Data-Grounded Parameterized Query Tools
            </p>
          </div>
        </div>
      </div>

      {/* CHAT STREAM CONTAINER */}
      <div className="flex-1 overflow-y-auto glass-card p-6 rounded-2xl space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-3xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
              msg.role === 'user' ? 'bg-tennis-green text-background-main' : 'bg-background-card border border-slateBorder text-tennis-green'
            }`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className={`space-y-2.5 rounded-2xl p-4 text-sm leading-relaxed ${
              msg.role === 'user'
                ? 'bg-tennis-green text-background-main font-medium'
                : 'bg-background-secondary border border-slateBorder text-textPrimary'
            }`}>
              <div className="whitespace-pre-line">{msg.content}</div>

              {/* Citations Badges */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-2 border-t border-slateBorder/40 flex flex-wrap items-center gap-1.5 text-xs">
                  <span className="text-[10px] uppercase font-mono text-textMuted flex items-center gap-1">
                    <Database className="w-3 h-3 text-tennis-green" /> Cited Sources:
                  </span>
                  {msg.citations.map((c, cIdx) => (
                    <span key={cIdx} className="px-2 py-0.5 rounded bg-background-card border border-slateBorder/60 text-[11px] text-tennis-green font-mono">
                      {c.label} ({c.reference_id})
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 max-w-3xl">
            <div className="w-8 h-8 rounded-xl bg-background-card border border-slateBorder flex items-center justify-center text-tennis-green shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-background-secondary border border-slateBorder rounded-2xl p-4 text-xs font-mono text-textMuted flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-tennis-green animate-ping"></span>
              Consulting database analytics & ML trait models...
            </div>
          </div>
        )}
      </div>

      {/* SUGGESTED PILLS */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[10px] font-mono uppercase text-textMuted flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-tennis-green" /> Suggested:
        </span>
        {STARTER_PROMPTS.map((prompt, pIdx) => (
          <button
            key={pIdx}
            onClick={() => handleSend(prompt)}
            className="px-3 py-1.5 rounded-xl bg-background-card hover:bg-background-cardHover border border-slateBorder/60 text-textSecondary hover:text-white shrink-0 transition"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* INPUT BAR */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="glass-card p-2 rounded-2xl flex items-center gap-2"
      >
        <input
          type="text"
          placeholder="Ask anything about rankings, player traits, tournament venues..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-transparent px-4 py-2.5 text-sm text-white placeholder-textMuted focus:outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-4 py-2.5 rounded-xl bg-tennis-green disabled:opacity-40 text-background-main font-bold text-sm hover:bg-tennis-greenHover transition flex items-center gap-1.5 shadow-md shadow-tennis-green/20"
        >
          <span>Ask</span> <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
