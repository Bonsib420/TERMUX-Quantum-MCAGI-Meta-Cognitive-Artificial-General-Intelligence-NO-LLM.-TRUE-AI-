import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function CistercianExplorer() {
  const [number, setNumber] = useState(1234);
  const [size, setSize] = useState(120);
  const [color, setColor] = useState('#FFFFFF');
  const [svgData, setSvgData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [batchRange, setBatchRange] = useState({ start: 0, end: 99 });
  const [message, setMessage] = useState('');

  // Fetch SVG on number/size/color change
  useEffect(() => {
    fetchSVG();
  }, [number, size, color]);

  const fetchSVG = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/cistercian/download`, {
        params: { number, size, color },
        responseType: 'text',
      });
      setSvgData(response.data);
      setMessage('');
    } catch (error) {
      setMessage(`Error: ${error.message}`);
      setSvgData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleNumberChange = (e) => {
    const val = parseInt(e.target.value) || 0;
    setNumber(Math.min(9999, Math.max(0, val)));
  };

  const adjustNumber = (delta) => {
    setNumber((prev) => Math.min(9999, Math.max(0, prev + delta)));
  };

  const downloadSingle = async () => {
    try {
      const response = await axios.get(`${API_BASE}/cistercian/download`, {
        params: { number, size, color },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `cistercian_${number.toString().padStart(4, '0')}.svg`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setMessage(`Downloaded ${number}.svg`);
    } catch (error) {
      setMessage(`Download failed: ${error.message}`);
    }
  };

  const downloadBatch = async () => {
    const { start, end } = batchRange;
    if (end - start + 1 > 1000) {
      setMessage('Batch too large! Maximum 1000 numerals per request.');
      return;
    }
    try {
      const response = await axios.get(`${API_BASE}/cistercian/batch`, {
        params: { start, end, size, color },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `cistercian_${start.toString().padStart(4, '0')}-${end.toString().padStart(4, '0')}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setMessage(`Downloaded ${start}-${end}.zip`);
    } catch (error) {
      setMessage(`Batch download failed: ${error.message}`);
    }
  };

  // Quick select buttons for thousands, hundreds, tens, ones
  const digits = [
    { label: 'Thousands', value: Math.floor(number / 1000), factor: 1000 },
    { label: 'Hundreds', value: Math.floor((number % 1000) / 100), factor: 100 },
    { label: 'Tens', value: Math.floor((number % 100) / 10), factor: 10 },
    { label: 'Ones', value: number % 10, factor: 1 },
  ];

  const adjustDigit = (digitIndex, delta) => {
    const digit = digits[digitIndex];
    const current = digits[digitIndex].value;
    const newValue = Math.min(9, Math.max(0, current + delta));
    const currentAbs = digit.value * digit.factor;
    const newAbs = newValue * digit.factor;
    setNumber((prev) => {
      const newNum = prev - currentAbs + newAbs;
      return Math.min(9999, Math.max(0, newNum));
    });
  };

  return (
    <div className="explorer">
      <div className="card">
        <h2>🔢 Numeral Display</h2>
        <div className="svg-container" style={{ background: '#000', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
          {loading ? (
            <div style={{ color: '#888', textAlign: 'center' }}>Loading...</div>
          ) : svgData ? (
            <div
              dangerouslySetInnerHTML={{ __html: svgData }}
              style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}
            />
          ) : (
            <div style={{ color: '#f44', textAlign: 'center' }}>{message || 'No SVG'}</div>
          )}
        </div>

        {message && <div className="message" style={{ color: '#ff6b6b', marginBottom: '1rem' }}>{message}</div>}

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <label>
            Number (0-9999):
            <input
              type="number"
              min="0"
              max="9999"
              value={number}
              onChange={handleNumberChange}
              className="input"
              style={{ width: '120px', marginLeft: '0.5rem' }}
            />
          </label>

          <label>
            Size: {size}px
            <input
              type="range"
              min="40"
              max="300"
              value={size}
              onChange={(e) => setSize(parseInt(e.target.value))}
              style={{ marginLeft: '0.5rem' }}
            />
          </label>

          <label>
            Color:
            <input
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              style={{ marginLeft: '0.5rem', width: '50px', height: '40px', border: 'none' }}
            />
          </label>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <button className="btn btn-secondary" onClick={() => adjustNumber(-1)}>◀ -1</button>
          <button className="btn btn-primary" onClick={() => adjustNumber(1)}>+1 ▶</button>
          <button className="btn btn-secondary" onClick={() => setNumber(0)}>Reset</button>
          <button className="btn btn-primary" onClick={downloadSingle}>⬇ Download SVG</button>
        </div>

        <div style={{ marginTop: '1rem' }}>
          <h4>Quick Digit Selection:</h4>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
            {digits.map((digit, idx) => (
              <div key={digit.label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.9rem', color: '#888' }}>{digit.label}:</span>
                <button className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem' }} onClick={() => adjustDigit(idx, -1)}>-</button>
                <span style={{ width: '30px', textAlign: 'center', fontWeight: 'bold', fontSize: '1.1rem' }}>{digit.value}</span>
                <button className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem' }} onClick={() => adjustDigit(idx, 1)}>+</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2>📦 Batch Download</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label>Start:</label>
            <input
              type="number"
              min="0"
              max="9999"
              value={batchRange.start}
              onChange={(e) => setBatchRange({ ...batchRange, start: Math.min(9999, Math.max(0, parseInt(e.target.value) || 0)) })}
              className="input"
              style={{ width: '100px' }}
            />
          </div>
          <div>
            <label>End:</label>
            <input
              type="number"
              min="0"
              max="9999"
              value={batchRange.end}
              onChange={(e) => setBatchRange({ ...batchRange, end: Math.min(9999, Math.max(0, parseInt(e.target.value) || 0)) })}
              className="input"
              style={{ width: '100px' }}
            />
          </div>
          <div style={{ color: '#888', fontSize: '0.9rem' }}>
            ({batchRange.end - batchRange.start + 1} numerals)
            {batchRange.end - batchRange.start + 1 > 1000 && (
              <span style={{ color: '#ff6b6b', marginLeft: '0.5rem' }}>Max 1000!</span>
            )}
          </div>
          <button
            className="btn btn-primary"
            onClick={downloadBatch}
            disabled={batchRange.end - batchRange.start + 1 > 1000}
          >
            ⬇ Download ZIP
          </button>
        </div>
      </div>
    </div>
  );
}

export default CistercianExplorer;
