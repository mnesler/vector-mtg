'use client';

import { useState, useEffect, useRef } from 'react';

interface SearchBarProps {
  placeholder?: string;
  className?: string;
}

export default function SearchBar({
  placeholder = "Search cards...",
  className = ""
}: SearchBarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Placeholder for WebSocket connection
    // TODO: Replace with actual WebSocket URL when backend is ready
    // wsRef.current = new WebSocket('ws://localhost:8080/search');

    // wsRef.current.onmessage = (event) => {
    //   const results = JSON.parse(event.data);
    //   // Handle search results
    // };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);

    // Placeholder for WebSocket search
    // if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
    //   wsRef.current.send(JSON.stringify({ query }));
    // }
  };

  return (
    <div className={`flex justify-center ${className}`}>
      <input
        type="search"
        placeholder={placeholder}
        value={searchQuery}
        onChange={handleSearchChange}
        className="input variant-form-material w-full max-w-2xl px-4 py-3 rounded-lg"
        aria-label="Search cards"
      />
    </div>
  );
}
