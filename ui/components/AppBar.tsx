'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

interface AppBarProps {
  onMenuClick?: () => void;
  onUserClick?: () => void;
}

const themes = [
  { name: 'wintry', label: 'Blue', emoji: '💧' },
  { name: 'modern', label: 'White', emoji: '☀️' },
  { name: 'crimson', label: 'Red', emoji: '🔥' },
  { name: 'seafoam', label: 'Green', emoji: '🌲' },
  { name: 'vintage', label: 'Black', emoji: '💀' },
  { name: 'miami', label: 'Miami', emoji: '🌴' },
];

export default function AppBar({ onMenuClick, onUserClick }: AppBarProps) {
  const router = useRouter();
  const [currentTheme, setCurrentTheme] = useState('wintry');
  const [isThemeOpen, setIsThemeOpen] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'wintry';
    setCurrentTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);

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

  const handleUserClick = () => {
    if (onUserClick) {
      onUserClick();
    }
    router.push('/user');
  };

  const handleThemeChange = (themeName: string) => {
    setCurrentTheme(themeName);
    localStorage.setItem('theme', themeName);
    document.documentElement.setAttribute('data-theme', themeName);

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

    setIsThemeOpen(false);
  };

  const currentThemeData = themes.find(t => t.name === currentTheme) || themes[0];

  return (
    <header className="app-bar w-full bg-surface-100-900 shadow-md">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Menu Icon */}
        <button
          type="button"
          onClick={onMenuClick}
          className="btn btn-icon variant-ghost-surface"
          aria-label="Open menu"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Center: Title */}
        <div className="flex-1 text-center">
          <h1 className="text-xl font-bold">MTG Vector DB</h1>
        </div>

        {/* Right: Theme Switcher & User Icon */}
        <div className="flex items-center gap-2">
          {/* Theme Switcher */}
          <div className="relative">
            <button
              onClick={() => setIsThemeOpen(!isThemeOpen)}
              className="btn btn-icon variant-ghost-surface"
              aria-label="Theme selector"
            >
              <span>{currentThemeData.emoji}</span>
            </button>

            {isThemeOpen && (
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

          {/* User Icon */}
          <button
            type="button"
            onClick={handleUserClick}
            className="btn btn-icon variant-ghost-surface"
            aria-label="User menu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
