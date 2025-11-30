'use client';

import { useState, useEffect } from 'react';

const themes = [
  { name: 'wintry', label: 'Blue', emoji: '💧' },      // Blue - Water/Islands
  { name: 'modern', label: 'White', emoji: '☀️' },      // White - Sun/Plains
  { name: 'crimson', label: 'Red', emoji: '🔥' },      // Red - Fire/Mountains
  { name: 'seafoam', label: 'Green', emoji: '🌲' },    // Green - Forest
  { name: 'vintage', label: 'Black', emoji: '💀' },    // Black - Skull/Swamp
  { name: 'miami', label: 'Miami', emoji: '🌴' },      // Miami - Special theme
];

export default function ThemeSwitcher() {
  const [currentTheme, setCurrentTheme] = useState('wintry');
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'wintry';
    setCurrentTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);

    // Apply theme backgrounds
    if (savedTheme === 'miami') {
      document.body.style.backgroundImage = 'url(/images/miami-background.jpg)';
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundPosition = 'center';
      document.body.style.backgroundAttachment = 'fixed';
    } else if (savedTheme === 'seafoam') {
      document.body.style.backgroundImage = 'url(/images/green.webp)';
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundPosition = 'center';
      document.body.style.backgroundAttachment = 'fixed';
    }
  }, []);

  const handleThemeChange = (themeName: string) => {
    setCurrentTheme(themeName);
    localStorage.setItem('theme', themeName);
    document.documentElement.setAttribute('data-theme', themeName);

    // Apply theme backgrounds
    if (themeName === 'miami') {
      document.body.style.backgroundImage = 'url(/images/miami-background.jpg)';
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundPosition = 'center';
      document.body.style.backgroundAttachment = 'fixed';
    } else if (themeName === 'seafoam') {
      document.body.style.backgroundImage = 'url(/images/green.webp)';
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundPosition = 'center';
      document.body.style.backgroundAttachment = 'fixed';
    } else {
      document.body.style.backgroundImage = 'none';
    }

    setIsOpen(false);
  };

  const currentThemeData = themes.find(t => t.name === currentTheme) || themes[0];

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="btn variant-filled-primary px-4 py-2 rounded-lg shadow-lg hover:scale-105 transition-transform flex items-center gap-2"
          aria-label="Theme selector"
        >
          <span>{currentThemeData.emoji}</span>
          <span className="hidden sm:inline">Themes</span>
          <span className="text-sm">{isOpen ? '▲' : '▼'}</span>
        </button>

        {isOpen && (
          <div
            className="absolute top-full right-0 mt-2 card variant-filled-surface p-2 rounded-lg shadow-xl min-w-[160px] z-[100] bg-surface-900"
            style={
              currentTheme === 'miami' ? {
                backgroundImage: 'url(/images/miami-background.jpg)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              } : currentTheme === 'seafoam' ? {
                backgroundImage: 'url(/images/green.webp)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              } : {}
            }
          >
            {themes.map((theme) => (
              <button
                key={theme.name}
                onClick={() => handleThemeChange(theme.name)}
                className={`w-full px-4 py-2 rounded-lg text-left hover:variant-soft-primary transition-colors flex items-center gap-2 ${
                  currentTheme === theme.name ? 'variant-filled-primary' : ''
                }`}
              >
                <span>{theme.emoji}</span>
                <span>{theme.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
