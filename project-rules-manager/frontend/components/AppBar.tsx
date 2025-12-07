'use client';

interface AppBarProps {
  onMenuClick?: () => void;
  onUserClick?: () => void;
}

export default function AppBar({ onMenuClick, onUserClick }: AppBarProps) {
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
          <h1 className="text-xl font-bold">vector-mtg</h1>
        </div>

        {/* Right: User Icon */}
        <button
          type="button"
          onClick={onUserClick}
          className="btn btn-icon variant-ghost-surface"
          aria-label="User menu"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>
    </header>
  );
}
