import { useMemo } from 'react';
import './LunarClock.css';

/**
 * Lunar cycle: 708h total (354h day + 354h night).
 * SVG circle visualization with animated marker.
 */
const CYCLE_HOURS = 708;
const DAY_HOURS = 354;

export default function LunarClock({ lunarHour = 0 }) {
  const hour = Math.max(0, Math.min(lunarHour, CYCLE_HOURS));

  const { angle, isDay, phase, phasePct } = useMemo(() => {
    const a = (hour / CYCLE_HOURS) * 360 - 90; // -90 so 0 is at top
    const day = hour <= DAY_HOURS;
    const pct = Math.round((hour / CYCLE_HOURS) * 100);
    const ph = day ? 'Fase Diurna' : 'Fase Noturna';
    return { angle: a, isDay: day, phase: ph, phasePct: pct };
  }, [hour]);

  // Marker position on the circle
  const rad = (angle * Math.PI) / 180;
  const R = 90; // radius of the track
  const cx = 120 + R * Math.cos(rad);
  const cy = 120 + R * Math.sin(rad);

  return (
    <section className="lunar-clock animate-slide-up" style={{ animationDelay: '0.4s' }}>
      <div className="clock-card glass-card">
        <h2 className="section-title">🌗 Ciclo Lunar</h2>

        <div className="clock-svg-wrapper">
          <svg viewBox="0 0 240 240" className="clock-svg">
            <defs>
              {/* Day arc gradient */}
              <linearGradient id="dayGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.3" />
              </linearGradient>
              {/* Night arc gradient */}
              <linearGradient id="nightGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#0a0e1a" stopOpacity="0.5" />
              </linearGradient>
              {/* Glow filter */}
              <filter id="markerGlow">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Background ring */}
            <circle cx="120" cy="120" r={R} fill="none" stroke="rgba(148,163,184,0.06)" strokeWidth="20" />

            {/* Day half (top arc: from -90° to +90° → 0 to 180° path) */}
            <path
              d={describeArc(120, 120, R, -90, 90)}
              fill="none"
              stroke="url(#dayGrad)"
              strokeWidth="20"
              strokeLinecap="round"
            />

            {/* Night half (bottom arc: from +90° to +270° → 180° to 360° path) */}
            <path
              d={describeArc(120, 120, R, 90, 270)}
              fill="none"
              stroke="url(#nightGrad)"
              strokeWidth="20"
              strokeLinecap="round"
            />

            {/* Tick marks */}
            {[0, 90, 180, 270].map((deg) => {
              const r1 = R - 14;
              const r2 = R + 14;
              const rr = (deg - 90) * Math.PI / 180;
              return (
                <line
                  key={deg}
                  x1={120 + r1 * Math.cos(rr)}
                  y1={120 + r1 * Math.sin(rr)}
                  x2={120 + r2 * Math.cos(rr)}
                  y2={120 + r2 * Math.sin(rr)}
                  stroke="rgba(148,163,184,0.15)"
                  strokeWidth="1"
                />
              );
            })}

            {/* Labels */}
            <text x="120" y="22" textAnchor="middle" className="clock-label day-label">☀️ Dia</text>
            <text x="120" y="230" textAnchor="middle" className="clock-label night-label">🌙 Noite</text>

            {/* Progress trail */}
            <circle
              cx="120" cy="120" r={R}
              fill="none"
              stroke={isDay ? '#00d4ff' : '#7c3aed'}
              strokeWidth="3"
              strokeDasharray={`${(phasePct / 100) * 2 * Math.PI * R} ${2 * Math.PI * R}`}
              strokeDashoffset={2 * Math.PI * R * 0.25}
              strokeLinecap="round"
              opacity="0.5"
            />

            {/* Marker */}
            <circle
              cx={cx}
              cy={cy}
              r="8"
              fill={isDay ? '#00d4ff' : '#7c3aed'}
              filter="url(#markerGlow)"
              className="clock-marker"
            />
            <circle cx={cx} cy={cy} r="4" fill="#fff" />

            {/* Center text */}
            <text x="120" y="112" textAnchor="middle" className="clock-center-value">
              {hour}h
            </text>
            <text x="120" y="132" textAnchor="middle" className="clock-center-label">
              de {CYCLE_HOURS}h
            </text>
          </svg>
        </div>

        <div className="clock-info">
          <div className={`clock-phase-badge ${isDay ? 'day' : 'night'}`}>
            {isDay ? '☀️' : '🌙'} {phase}
          </div>
          <div className="clock-progress-bar">
            <div
              className="clock-progress-fill"
              style={{
                width: `${phasePct}%`,
                background: isDay
                  ? 'linear-gradient(90deg, #00d4ff, #f59e0b)'
                  : 'linear-gradient(90deg, #7c3aed, #1e1b4b)',
              }}
            />
          </div>
          <span className="clock-pct font-mono">{phasePct}% do ciclo completo</span>
        </div>
      </div>
    </section>
  );
}

/* ---- Utility: SVG arc path ---- */
function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = ((angleDeg) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? '0' : '1';
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}
