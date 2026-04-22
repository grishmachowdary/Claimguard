import React, { useState } from 'react';
import { LANGUAGES } from '../i18n';
import { useLang } from '../context/LanguageContext';
import './LanguageSelector.css';

function LanguageSelector() {
  const { lang, changeLang } = useLang();
  const [open, setOpen] = useState(false);
  const current = LANGUAGES.find(l => l.code === lang) || LANGUAGES[0];

  return (
    <div className="lang-selector">
      <button className="lang-btn" onClick={() => setOpen(!open)}>
        <span>{current.flag}</span>
        <span>{current.label}</span>
        <span className="lang-arrow">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="lang-dropdown">
          {LANGUAGES.map(l => (
            <button
              key={l.code}
              className={`lang-option ${l.code === lang ? 'lang-active' : ''}`}
              onClick={() => { changeLang(l.code); setOpen(false); }}
            >
              <span>{l.flag}</span>
              <span>{l.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default LanguageSelector;
