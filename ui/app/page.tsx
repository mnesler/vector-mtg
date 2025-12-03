'use client';

import SearchBar from "../components/SearchBar";
import { useState, useEffect, useRef, useCallback } from "react";

interface Card {
  id: string;
  name: string;
  mana_cost: string;
  cmc: number;
  type_line: string;
  oracle_text: string;
  keywords: string[];
  similarity?: number;
}

export default function Home() {
  const [searchResults, setSearchResults] = useState<Card[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [currentMode, setCurrentMode] = useState<'keyword' | 'semantic'>('semantic');
  const observerTarget = useRef<HTMLTableRowElement>(null);

  const handleSearchResults = (results: Card[], query: string, mode: 'keyword' | 'semantic', hasMore: boolean) => {
    setSearchResults(results);
    setCurrentQuery(query);
    setCurrentMode(mode);
    setHasMore(hasMore);
    setIsSearching(false);
  };

  const handleSearchStart = () => {
    setIsSearching(true);
    setSearchResults([]);
    setHasMore(false);
  };

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoadingMore || !currentQuery) return;

    setIsLoadingMore(true);
    try {
      const endpoint = currentMode === 'keyword'
        ? `/api/cards/keyword?query=${encodeURIComponent(currentQuery)}&limit=10&offset=${searchResults.length}`
        : `/api/cards/hybrid?query=${encodeURIComponent(currentQuery)}&limit=10&offset=${searchResults.length}&threshold=0.50`;

      const response = await fetch(`http://localhost:8000${endpoint}`);
      if (!response.ok) throw new Error(`Search failed: ${response.statusText}`);

      const data = await response.json();
      setSearchResults(prev => [...prev, ...(data.cards || [])]);
      setHasMore(data.has_more || false);
    } catch (error) {
      console.error('Load more error:', error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasMore, isLoadingMore, currentQuery, currentMode, searchResults.length]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasMore, isLoadingMore, loadMore]);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8"></h1>

      <div className="w-full">
        {/* Search Bar */}
        <SearchBar 
          className="mb-8" 
          onSearchResults={handleSearchResults}
          onSearchStart={handleSearchStart}
        />

        {/* Results Table - Always Visible */}
        <div className="card bg-surface-100-900 shadow-xl">
          <div className="table-container">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Cost</th>
                  <th>Text</th>
                  {searchResults.length > 0 && searchResults[0]?.similarity && <th>Match</th>}
                </tr>
              </thead>
              <tbody>
                {isSearching ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12">
                      <div className="flex flex-col items-center gap-4">
                        <div className="animate-spin h-12 w-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
                        <p className="text-lg opacity-60">Searching...</p>
                      </div>
                    </td>
                  </tr>
                ) : searchResults.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12">
                      <p className="text-lg opacity-60">Use the search bar, Max</p>
                    </td>
                  </tr>
                ) : (
                  searchResults.map((card, index) => (
                    <tr 
                      key={card.id} 
                      className={`animate-fade-in ${index % 2 === 0 ? 'bg-surface-50-950/50' : ''}`}
                      ref={index === searchResults.length - 1 ? observerTarget : null}
                    >
                      <td className="font-semibold">{card.name}</td>
                      <td className="text-sm opacity-80">{card.type_line}</td>
                      <td className="font-mono text-sm">{card.mana_cost || '—'}</td>
                      <td className="text-sm opacity-80 max-w-md">
                        {card.oracle_text || <span className="opacity-50">No text</span>}
                      </td>
                      {card.similarity && (
                        <td className="text-sm">
                          <span className="badge variant-soft-primary">
                            {(card.similarity * 100).toFixed(1)}%
                          </span>
                        </td>
                      )}
                    </tr>
                  ))
                )}
                {isLoadingMore && (
                  <tr>
                    <td colSpan={5} className="text-center py-6">
                      <div className="flex items-center justify-center gap-2">
                        <div className="animate-spin h-6 w-6 border-2 border-primary-500 border-t-transparent rounded-full"></div>
                        <p className="text-sm opacity-60">Loading more...</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
