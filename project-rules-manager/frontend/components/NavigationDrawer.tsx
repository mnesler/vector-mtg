'use client';

import Link from 'next/link';
import { useState } from 'react';

interface NavigationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function NavigationDrawer({ isOpen, onClose }: NavigationDrawerProps) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-surface-100-900 shadow-xl z-50 transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <nav className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-surface-300-700">
            <h2 className="text-xl font-bold">Menu</h2>
          </div>

          {/* Navigation Links */}
          <div className="flex-1 p-4">
            <ul className="space-y-2">
              <li>
                <Link
                  href="/"
                  className="block px-4 py-3 rounded-lg hover:bg-surface-200-800 transition-colors"
                  onClick={onClose}
                >
                  Home
                </Link>
              </li>
              <li>
                <Link
                  href="/rules"
                  className="block px-4 py-3 rounded-lg hover:bg-surface-200-800 transition-colors"
                  onClick={onClose}
                >
                  Rules Browser
                </Link>
              </li>
              <li>
                <Link
                  href="/deck"
                  className="block px-4 py-3 rounded-lg hover:bg-surface-200-800 transition-colors"
                  onClick={onClose}
                >
                  Deck Analyzer
                </Link>
              </li>
            </ul>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-surface-300-700">
            <p className="text-sm opacity-60">vector-mtg v1.0</p>
          </div>
        </nav>
      </aside>
    </>
  );
}
