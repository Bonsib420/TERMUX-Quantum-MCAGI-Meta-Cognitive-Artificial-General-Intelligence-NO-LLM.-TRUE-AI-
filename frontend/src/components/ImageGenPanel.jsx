import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = '/api';

const ImageGenPanel = () => {
  const [prompt, setPrompt] = useState('');
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateImage = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setLoading(true);
    setError(null);
    setGeneratedImage(null);

    try {
      const response = await axios.post(`${API_BASE}/image/generate`, {
        prompt: prompt.trim(),
        width: parseInt(width),
        height: parseInt(height)
      });

      if (response.data && response.data.image) {
        setGeneratedImage(response.data.image);
      } else {
        setError('No image returned from server');
      }
    } catch (err) {
      console.error('Image generation failed:', err);
      setError(`Failed to generate image: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    if (!generatedImage) return;
    
    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = `quantum-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ 
      padding: '1rem', 
      height: '100%', 
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem'
    }}>
      <div style={{ 
        fontFamily: 'JetBrains Mono, monospace', 
        fontSize: '0.8rem', 
        color: '#a855f7',
        marginBottom: '0.5rem'
      }}>
        🎨 QUANTUM IMAGE GENERATOR
      </div>

      {/* Prompt Input */}
      <div>
        <label style={{ 
          display: 'block', 
          marginBottom: '0.5rem', 
          color: '#6b8299', 
          fontSize: '0.85rem',
          fontFamily: 'Space Grotesk, sans-serif'
        }}>
          Prompt (describe your image):
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., quantum consciousness mind reality universe..."
          style={{
            width: '100%',
            minHeight: '80px',
            background: '#0f1923',
            border: '1px solid #1a2a3e',
            color: '#c8d6e5',
            borderRadius: '8px',
            padding: '0.75rem',
            fontFamily: 'Space Grotesk, sans-serif',
            fontSize: '0.9rem',
            resize: 'vertical'
          }}
        />
      </div>

      {/* Dimensions */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.25rem', 
            color: '#6b8299', 
            fontSize: '0.75rem' 
          }}>
            Width
          </label>
          <input
            type="number"
            value={width}
            onChange={(e) => setWidth(e.target.value)}
            min={64}
            max={1024}
            step={64}
            style={{
              width: '100%',
              background: '#0f1923',
              border: '1px solid #1a2a3e',
              color: '#c8d6e5',
              borderRadius: '4px',
              padding: '0.5rem',
              fontFamily: 'JetBrains Mono, monospace'
            }}
          />
        </div>
        <div style={{ 
          fontSize: '1.2rem', 
          color: '#3d5570', 
          marginTop: '1.5rem' 
        }}>
          ×
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.25rem', 
            color: '#6b8299', 
            fontSize: '0.75rem' 
          }}>
            Height
          </label>
          <input
            type="number"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            min={64}
            max={1024}
            step={64}
            style={{
              width: '100%',
              background: '#0f1923',
              border: '1px solid #1a2a3e',
              color: '#c8d6e5',
              borderRadius: '4px',
              padding: '0.5rem',
              fontFamily: 'JetBrains Mono, monospace'
            }}
          />
        </div>
      </div>

      {/* Generate Button */}
      <button
        onClick={generateImage}
        disabled={loading || !prompt.trim()}
        style={{
          width: '100%',
          padding: '0.75rem',
          background: loading ? '#1a2a3e' : '#a855f7',
          border: `1px solid ${loading ? '#1a2a3e' : '#a855f7'}`,
          color: loading ? '#6b8299' : '#ffffff',
          borderRadius: '8px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.85rem',
          letterSpacing: '0.05em',
          transition: 'all 0.2s',
          opacity: loading || !prompt.trim() ? 0.5 : 1
        }}
      >
        {loading ? 'GENERATING...' : 'GENERATE IMAGE'}
      </button>

      {/* Error */}
      {error && (
        <div style={{
          padding: '0.75rem',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          color: '#ef4444',
          borderRadius: '8px',
          fontSize: '0.85rem',
          fontFamily: 'Space Grotesk, sans-serif'
        }}>
          {error}
        </div>
      )}

      {/* Generated Image */}
      {generatedImage && (
        <div style={{ 
          marginTop: '0.5rem', 
          display: 'flex', 
          flexDirection: 'column',
          gap: '0.5rem'
        }}>
          <div style={{
            border: '1px solid var(--border)',
            borderRadius: '8px',
            overflow: 'hidden',
            background: 'var(--bg-surface)',
            textAlign: 'center'
          }}>
            <img 
              src={generatedImage} 
              alt="Generated quantum art" 
              style={{
                maxWidth: '100%',
                height: 'auto',
                display: 'block'
              }}
            />
          </div>
          
          {/* Download Button */}
          <button
            onClick={downloadImage}
            style={{
              padding: '0.5rem',
              background: 'var(--bg-raised)',
              border: '1px solid var(--border)',
              color: 'var(--accent)',
              borderRadius: '8px',
              cursor: 'pointer',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.75rem',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.background = '#1a2a3e';
              e.target.style.borderColor = '#00e5a0';
            }}
            onMouseOut={(e) => {
              e.target.style.background = '#0f1923';
              e.target.style.borderColor = '#1a2a3e';
            }}
          >
            ⬇ DOWNLOAD PNG
          </button>

          {/* Info */}
          <div style={{
            color: '#3d5570',
            fontSize: '0.7rem',
            fontFamily: 'JetBrains Mono, monospace',
            textAlign: 'center'
          }}>
            {width}×{height} • Generated via Quantum Algorithms
          </div>
        </div>
      )}

      {/* Concepts Info */}
      <div style={{
        marginTop: 'auto',
        padding: '0.75rem',
        background: '#0f1923',
        border: '1px solid #1a2a3e',
        borderRadius: '8px',
        fontSize: '0.75rem',
        color: '#6b8299',
        fontFamily: 'JetBrains Mono, monospace'
      }}>
        <div style={{ color: '#a855f7', marginBottom: '0.5rem' }}>
          CONCEPTS
        </div>
        <div style={{ lineHeight: '1.6' }}>
          Keywords: consciousness, quantum, reality, mind, universe, time, law, god, nothingness, potential
        </div>
        <div style={{ marginTop: '0.5rem', color: '#3d5570' }}>
          Images are procedurally generated using quantum-inspired algorithms with semantic color mapping.
        </div>
      </div>
    </div>
  );
};

export default ImageGenPanel;
