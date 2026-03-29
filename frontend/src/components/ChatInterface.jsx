import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Capacitor } from '@capacitor/core';
import { Clipboard } from '@capacitor/clipboard';
import { generateStructuredResponse } from '../structuredGenerator';

const API_BASE = 'http://localhost:8000/api';

function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am Quantum MCAGI. Ask me anything about Cistercian numerals, quantum computing, or philosophy.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [explainMode, setExplainMode] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showNav, setShowNav] = useState(false);
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}`);
  const messagesEnd = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startNewChat = () => {
    setMessages([
      { role: 'assistant', content: 'New conversation started. How can I help you?' }
    ]);
    setSessionId(`session_${Date.now()}`);
  };

  const copyToClipboard = async (text) => {
    try {
      if (Capacitor.isNativePlatform()) {
        // Use Capacitor Clipboard plugin for native Android/iOS
        await Clipboard.write({ string: text });
        alert('Copied to clipboard!');
      } else if (navigator.clipboard) {
        // Use Web Clipboard API for browsers
        await navigator.clipboard.writeText(text);
        alert('Copied to clipboard!');
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (success) {
          alert('Copied to clipboard!');
        } else {
          throw new Error('Fallback copy failed');
        }
      }
    } catch (err) {
      console.error('Copy failed:', err);
      // Try alternative method as last resort
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (success) {
          alert('Copied to clipboard!');
        } else {
          alert('Failed to copy. Please try manually selecting the text.');
        }
      } catch (e) {
        alert('Failed to copy. Please select text manually and copy.');
      }
    }
  };
  };

  const exportForClaude = async () => {
    try {
      // Build markdown from current messages in state (works offline too)
      const lines = [];
      lines.push('# Quantum MCAGI — Chat Export');
      lines.push(`**Session:** \`${sessionId}\``);
      lines.push(`**Messages:** ${messages.length}`);
      lines.push(`**Exported:** ${new Date().toISOString()}`);
      lines.push('');
      lines.push('---');
      lines.push('');

      messages.forEach(msg => {
        if (msg.role === 'user') {
          lines.push('### 🧑 User');
        } else {
          lines.push('### 🔮 Quantum MCAGI');
        }
        lines.push('');
        lines.push(typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content));
        lines.push('');
        lines.push('---');
        lines.push('');
      });

      lines.push('');
      lines.push('> **Context for Claude:** This conversation is from Quantum MCAGI, a true AI system');
      lines.push('> built without LLMs. It uses quantum computing (PennyLane), Penrose Orch-OR');
      lines.push('> consciousness model, self-evolution, Markov chain language generation, and a');
      lines.push('> multi-layered cognitive architecture. The system runs on Termux (Android).');

      const exported = lines.join('\n');
      await copyToClipboard(exported);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed. Check console for details.');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // 1. Handle slash commands
      if (userMessage.content.startsWith('/research ')) {
        const parts = userMessage.content.split(' ');
        let depth = 10;
        const topicParts = [];
        parts.slice(1).forEach(p => {
          if (p.startsWith('-') && !isNaN(p.slice(1))) {
            depth = parseInt(p.slice(1));
          } else {
            topicParts.push(p);
          }
        });
        const topic = topicParts.join(' ');
        try {
          const res = await axios.post(`${API_BASE}/quantum/chat`, {
            content: `Give me ${depth} detailed research points about: ${topic}. Format as numbered list.`,
            mode: 'quantum',
            session_id: sessionId
          });
          setMessages(prev => [...prev, { role: 'assistant', content: `🔬 Research: ${topic}\n\n` + res.data.response }]);
        } catch(e) {
          setMessages(prev => [...prev, { role: 'assistant', content: `Research error: ${e.message}` }]);
        }
        setLoading(false);
        return;
      }

      // 1. Generate structured response locally (frontend)
      const structured = null;

      // 2. Send user input + structured response to backend for Markov weaving
      const response = await axios.post(`${API_BASE}/quantum/chat`, {
        content: userMessage.content,
        structured_response: structured,
        mode: 'quantum',
        explain_mode: explainMode,
        session_id: sessionId
      });

      let messageContent = response.data.response;
      if (explainMode && response.data.explanation) {
        const exp = response.data.explanation;
        const explanationText = `\n\n--- EXPLANATION ---\n` +
          `Path: ${exp.reasoning_path?.join(' → ') || 'N/A'}\n` +
          `Confidence: ${(exp.confidence_score * 10).toFixed(1)}%\n` +
          `Engines: ${exp.engines_used?.join(', ') || 'N/A'}\n` +
          `\nSteps:\n${(exp.steps || []).map((s,i) => `${i+1}. ${s.step}`).join('\n')}`;
        messageContent += explanationText;
      }

      const assistantMessage = { role: "assistant", content: String(messageContent) };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Upload file to server (endpoint: /api/explorer/upload)
      const uploadResponse = await axios.post(`${API_BASE}/explorer/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(`File uploaded: ${uploadResponse.data.filename}`);
      // Optionally add a system message
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `📄 Uploaded "${uploadResponse.data.filename}" (${uploadResponse.data.size} bytes). You can now ask questions about it.`
      }]);
    } catch (error) {
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  const navLinks = [
    { label: 'Home', href: '/app/', icon: '🏠' },
    { label: 'Explorer', href: '/app/explorer', icon: '📂' },
    { label: 'Cognitive', href: '/app/cognitive', icon: '🧠' },
    { label: 'Brain', href: '/app/brain', icon: '🔮' },
    { label: 'Media', href: '/app/media', icon: '🎬' },
    { label: 'Settings', href: '/app/settings', icon: '⚙️' },
  ];

  const QuickCommandButton = ({ label, command, onClick }) => (
    <button
      onClick={() => {
        if (command) {
          setInput(`/${command} `);
        } else if (onClick) {
          onClick();
        }
      }}
      style={{
        padding: '0.4rem 0.8rem',
        margin: '0.25rem',
        background: '#1a3a5c',
        border: '1px solid #2a5a8c',
        color: '#6ee7b7',
        borderRadius: '12px',
        cursor: 'pointer',
        fontSize: '0.85rem'
      }}
    >
      {label}
    </button>
  );

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0a0a0a', color: '#e0e0e0' }}>
      {/* Left Sidebar - Chat History */}
      <div style={{
        width: showHistory ? 260 : 0,
        background: '#111',
        borderRight: '1px solid #333',
        transition: 'width 0.3s',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, color: '#00d4ff' }}>History</h3>
          <button onClick={() => setShowHistory(false)} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer' }}>✕</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
          <p style={{ color: '#666', fontSize: '0.8rem' }}>Recent conversations will appear here.</p>
        </div>
      </div>

      {/* Right Sidebar - Navigation */}
      <div style={{
        width: showNav ? 220 : 0,
        background: '#111',
        borderLeft: '1px solid #333',
        transition: 'width 0.3s',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, color: '#00d4ff' }}>Menu</h3>
          <button onClick={() => setShowNav(false)} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer' }}>✕</button>
        </div>
        <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {navLinks.map(link => (
            <a key={link.href} href={link.href} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem',
              color: '#6ee7b7',
              textDecoration: 'none',
              borderRadius: '8px',
              background: '#1a1a1a',
              border: '1px solid #333'
            }}>
              <span>{link.icon}</span>
              <span>{link.label}</span>
            </a>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Bar */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.75rem 1rem',
          background: '#111',
          borderBottom: '1px solid #333'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setShowHistory(!showHistory)}
              style={{
                background: showHistory ? '#2a5a8c' : '#1a1a1a',
                border: '1px solid #333',
                color: '#00d4ff',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              {showHistory ? '← Hide History' : 'History'}
            </button>
            <button
              onClick={() => setShowNav(!showNav)}
              style={{
                background: showNav ? '#2a5a8c' : '#1a1a1a',
                border: '1px solid #333',
                color: '#00d4ff',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              {showNav ? 'Hide Menu' : 'Menu'}
            </button>
          </div>
          <h2 style={{ margin: 0, color: '#00d4ff', fontSize: '1.2rem' }}>Quantum MCAGI</h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={exportForClaude}
              style={{
                background: '#2a1a3c',
                border: '1px solid #6b46c1',
                color: '#d6bcfa',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
              title="Export this conversation as markdown — copies to clipboard, ready to paste into Claude"
            >
              📤 Share w/ Claude
            </button>
            <button
              onClick={startNewChat}
              style={{
                background: '#1a3a5c',
                border: '1px solid #2a5a8c',
                color: '#6ee7b7',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              + New Chat
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="messages" style={{ flex: 1, overflowY: 'auto', padding: '1rem', background: '#0a0a0a' }}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                marginBottom: '1rem',
                alignItems: 'flex-start',
                gap: '0.5rem'
              }}
            >
              <div style={{
                flex: 1,
                marginRight: 'auto',
                maxWidth: '85%'
              }}>
                <div style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '12px',
                  background: msg.role === 'user' ? '#1a3a5c' : '#1a1a1a',
                  border: msg.role === 'user' ? '1px solid #2a5a8c' : '1px solid #333',
                  position: 'relative'
                }}>
                  <div style={{
                    fontWeight: 'bold',
                    marginBottom: '0.25rem',
                    color: msg.role === 'user' ? '#6ee7b7' : '#00d4ff',
                    fontSize: '0.9rem'
                  }}>
                    {msg.role === 'user' ? 'You' : 'Quantum MCAGI'}
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)}</div>
                  <button
                    onClick={() => copyToClipboard(msg.content)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#888',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      padding: '4px',
                      float: 'right'
                    }}
                    title="Copy to clipboard"
                  >
                    📋
                  </button>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ color: '#888', fontStyle: 'italic', padding: '0.5rem' }}>Quantum MCAGI is thinking...</div>
          )}
          <div ref={messagesEnd} />
        </div>

        {/* Quick Commands Bar */}
        <div style={{
          padding: '0.5rem 1rem',
          background: '#111',
          borderTop: '1px solid #333',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.25rem'
        }}>
          <QuickCommandButton label="💡 Explain" command="explain" />
          <QuickCommandButton label="📊 Status" command="status" />
          <QuickCommandButton label="💾 Save" command="save" />
          <QuickCommandButton label="☁️ Cloud" command="cloud-status" />
          <QuickCommandButton label="🧠 Knowledge" command="knowledge" />
          <QuickCommandButton label="📈 Analyze" command="analyze" />
          <QuickCommandButton label="🎭 Personality" command="personality" />
          <QuickCommandButton label="🔍 Collapse" command="collapse" />
          <QuickCommandButton label="📤 Export" command="export" />
        </div>

        {/* Input Area */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          padding: '1rem',
          background: '#111',
          borderTop: '1px solid #333',
          alignItems: 'center'
        }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            style={{
              background: '#1a1a1a',
              border: '1px solid #333',
              color: '#00d4ff',
              padding: '0.75rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1.2rem'
            }}
            title="Attach file"
          >
            📎
          </label>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about Cistercian numerals, quantum philosophy, or anything..."
            style={{
              flex: 1,
              resize: 'none',
              height: '60px',
              minHeight: '60px',
              maxHeight: '120px',
              background: '#1a1a1a',
              border: '1px solid #333',
              color: '#e0e0e0',
              borderRadius: '8px',
              padding: '0.75rem'
            }}
            disabled={loading}
          />
          <button
            onClick={() => setExplainMode(!explainMode)}
            style={{
              background: explainMode ? '#00d4ff' : '#1a1a1a',
              border: `1px solid ${explainMode ? '#00d4ff' : '#333'}`,
              color: explainMode ? '#000' : '#00d4ff',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
            title="Toggle explanation mode"
          >
            {explainMode ? '🔬 EXPLAIN ON' : 'Explain'}
          </button>
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim() ? '#333' : '#00d4ff',
              color: loading || !input.trim() ? '#666' : '#000',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '1rem'
            }}
          >
            Send
          </button>
        </div>

        {/* Footer */}
        <div style={{
          padding: '0.5rem 1rem',
          background: '#0a0a0a',
          borderTop: '1px solid #222',
          color: '#666',
          fontSize: '0.75rem',
          textAlign: 'center'
        }}>
          Quantum MCAGI • Local Storage • PennyLane Quantum • Tap any message to copy
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
