import { useState, useEffect } from 'react';
import './Header.css';

export default function Header({ status, error }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const isOnline = !!status && !error;
  const riskLevel = status?.risk_level || 'unknown';

  const riskConfig = {
    low:      { label: 'BAIXO',    class: 'badge-green' },
    medium:   { label: 'MÉDIO',    class: 'badge-amber' },
    high:     { label: 'ALTO',     class: 'badge-red' },
    critical: { label: 'CRÍTICO',  class: 'badge-red' },
    unknown:  { label: 'N/D',      class: 'badge-purple' },
  };

  const risk = riskConfig[riskLevel] || riskConfig.unknown;

  return (
    <header className="header">
      <div className="header-left">
        <div className="logo-group">
          <div className="logo-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <circle cx="16" cy="16" r="14" stroke="url(#logoGrad)" strokeWidth="2" />
              <path d="M16 4 C20 10, 20 22, 16 28 C12 22, 12 10, 16 4Z" fill="url(#logoGrad)" opacity="0.6" />
              <circle cx="16" cy="16" r="4" fill="#00d4ff" />
              <defs>
                <linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32">
                  <stop offset="0%" stopColor="#00d4ff" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div>
            <h1 className="logo-text">
              Lunar<span className="logo-accent">Grid</span>
            </h1>
            <p className="logo-subtitle">Sistema de Gerenciamento Energético Lunar</p>
          </div>
        </div>
      </div>

      <div className="header-right">
        <div className="header-meta">
          <span className="header-time font-mono">
            {time.toLocaleTimeString('en-US', { hour12: false })} UTC
          </span>
          <span className={`badge ${risk.class}`}>
            ⚡ RISCO: {risk.label}
          </span>
        </div>
        <div className={`connection-status ${isOnline ? 'online' : 'offline'}`}>
          <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
          <span className="connection-label">
            {isOnline ? 'Conectado' : 'Desconectado'}
          </span>
        </div>
      </div>
    </header>
  );
}
