'use client';

export default function UserPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">User Profile</h1>

      <div className="card p-6 bg-surface-100-900 shadow-xl">
        <div className="flex items-center mb-6">
          <div className="w-24 h-24 rounded-full bg-primary-500 flex items-center justify-center text-white text-4xl font-bold mr-6">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-2">MTG Player</h2>
            <p className="text-surface-600-400">Member since 2025</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="border-t border-surface-300-700 pt-6">
            <h3 className="text-xl font-semibold mb-4">Profile Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium opacity-60">Username</label>
                <p className="text-lg">player_one</p>
              </div>
              <div>
                <label className="text-sm font-medium opacity-60">Email</label>
                <p className="text-lg">player@example.com</p>
              </div>
            </div>
          </div>

          <div className="border-t border-surface-300-700 pt-6">
            <h3 className="text-xl font-semibold mb-4">Statistics</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card p-4 bg-surface-200-800">
                <p className="text-sm opacity-60 mb-1">Decks Created</p>
                <p className="text-3xl font-bold text-primary-500">0</p>
              </div>
              <div className="card p-4 bg-surface-200-800">
                <p className="text-sm opacity-60 mb-1">Cards Searched</p>
                <p className="text-3xl font-bold text-secondary-500">0</p>
              </div>
              <div className="card p-4 bg-surface-200-800">
                <p className="text-sm opacity-60 mb-1">Rules Browsed</p>
                <p className="text-3xl font-bold text-tertiary-500">0</p>
              </div>
            </div>
          </div>

          <div className="border-t border-surface-300-700 pt-6">
            <h3 className="text-xl font-semibold mb-4">Preferences</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-surface-200-800 rounded-lg">
                <span>Email Notifications</span>
                <input type="checkbox" className="toggle" />
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-200-800 rounded-lg">
                <span>Show Card Prices</span>
                <input type="checkbox" className="toggle" defaultChecked />
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-200-800 rounded-lg">
                <span>Auto-save Searches</span>
                <input type="checkbox" className="toggle" defaultChecked />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
