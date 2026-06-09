import Header from './components/Header';
import Dashboard from './components/Dashboard';
import SectorPanel from './components/SectorPanel';
import StressSimulator from './components/StressSimulator';
import LunarClock from './components/LunarClock';
import { useTelemetry } from './hooks/useTelemetry';
import './App.css';

export default function App() {
  const { status, loading, error, refetch } = useTelemetry(5000);

  return (
    <div className="app">
      <Header status={status} error={error} />

      <main className="app-main">
        {/* Connection error banner */}
        {error && !loading && (
          <div className="connection-banner animate-fade-in">
            <span className="connection-banner-icon">📡</span>
            <div>
              <strong>Conexão Perdida</strong>
              <p>Não foi possível conectar ao servidor da API. Exibindo dados de fallback. Tentando reconectar a cada 5 segundos…</p>
            </div>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && !status && (
          <div className="loading-screen">
            <div className="loading-spinner" />
            <p>Estabelecendo conexão com a Base Lunar…</p>
          </div>
        )}

        {/* Main grid */}
        <div className="app-grid">
          <div className="app-col-left">
            <Dashboard status={status} />
            <StressSimulator onRefetch={refetch} />
          </div>
          <div className="app-col-right">
            <SectorPanel status={status} onRefetch={refetch} />
            <LunarClock lunarHour={status?.lunar_hour ?? 180} />
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <span>LunarGrid — Controle de Missão</span>
        <span className="text-muted">•</span>
        <span className="text-muted">v1.0.0</span>
      </footer>
    </div>
  );
}
