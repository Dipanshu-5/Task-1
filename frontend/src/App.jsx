import React from "react";
import LogInteractionPage from "./pages/LogInteractionPage";
import "./styles/index.css";

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-container">
          <div className="logo-icon">α</div>
          <div className="logo-details">
            <span className="logo-text">AuraCRM</span>
          </div>
          <span className="app-title-badge">HCP Log Module</span>
        </div>
        <div className="header-status">
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--sentiment-pos)', display: 'inline-block' }}></span>
            Active Session
          </span>
        </div>
      </header>
      <main>
        <LogInteractionPage />
      </main>
    </div>
  );
}

export default App;
