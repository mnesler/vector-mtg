'use client';

import SearchBar from "../components/SearchBar";
import Tag from "../components/Tag";
import DashboardCard from "../components/DashboardCard";
import { GRADIENTS } from "../components/Gradients";
import { useState, useEffect, useRef, useCallback } from "react";

interface TagData {
  id: number;
  name: string;
  display_name?: string;
  category?: string;
  confidence?: number;
}

interface Card {
  id: string;
  name: string;
  mana_cost: string;
  cmc: number;
  type_line: string;
  oracle_text: string;
  keywords: string[];
  similarity?: number;
  tags?: TagData[];
}

interface TagStats {
  total_playable_cards: number;
  total_cards_with_tags: number;
  high_confidence_cards: number;
  low_confidence_cards: number;
  average_confidence: number;
}

export default function Home() {
  const [searchResults, setSearchResults] = useState<Card[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [currentMode, setCurrentMode] = useState<'keyword' | 'semantic'>('semantic');
  const [tagStats, setTagStats] = useState<TagStats | null>(null);
  const observerTarget = useRef<HTMLTableRowElement>(null);

  // Fetch tag statistics on mount
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/stats/tags');
        if (response.ok) {
          const data = await response.json();
          setTagStats(data);
        }
      } catch (error) {
        console.error('Failed to fetch tag statistics:', error);
      }
    };
    fetchStats();
  }, []);

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
        ? `/api/cards/keyword?query=${encodeURIComponent(currentQuery)}&limit=10&offset=${searchResults.length}&include_tags=true&tags=true`
        : `/api/cards/semantic?query=${encodeURIComponent(currentQuery)}&limit=10&offset=${searchResults.length}&include_tags=true&tags=true`;

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

        {/* Dashboard Cards */}
        {tagStats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <DashboardCard
              title="Cards with Tags"
              value={
                <span>
                  {tagStats.total_cards_with_tags}
                  <span className="text-2xl font-normal opacity-70 ml-2">
                    ({tagStats.total_playable_cards.toLocaleString()})
                  </span>
                </span>
              }
              gradient={GRADIENTS[0]}
              subtitle="Tagged cards (total playable cards)"
            />
            <DashboardCard
              title="High Confidence"
              value={
                <span>
                  {tagStats.high_confidence_cards}
                  <span className="text-2xl font-normal opacity-70 ml-2">
                    ({(tagStats.average_confidence * 100).toFixed(1)}%)
                  </span>
                </span>
              }
              gradient={GRADIENTS[1]}
              subtitle="Cards ≥70% confidence (avg confidence)"
            />
            <DashboardCard
              title="Low Confidence"
              value={tagStats.low_confidence_cards}
              gradient={GRADIENTS[2]}
              subtitle="Cards with <70% confidence tags"
            />
          </div>
        )}

        {/* Results Table - Always Visible */}
        <div className="card bg-surface-100-900 shadow-xl">
          <div className="table-container">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Tags</th>
                  <th>Type</th>
                  <th>Cost</th>
                  <th>Text</th>
                  {searchResults.length > 0 && searchResults[0]?.similarity && <th>Match</th>}
                </tr>
              </thead>
              <tbody>
                {isSearching ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12">
                      <div className="flex flex-col items-center gap-4">
                        <div className="animate-spin h-12 w-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
                        <p className="text-lg opacity-60">Searching...</p>
                      </div>
                    </td>
                  </tr>
                ) : searchResults.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12">
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
                      <td className="text-sm">
                        <div className="flex flex-wrap gap-1">
                          {card.tags && card.tags.length > 0 ? (
                            card.tags.slice(0, 5).map((tag) => (
                              <Tag
                                key={tag.id}
                                name={tag.name}
                                displayName={tag.display_name}
                                confidence={tag.confidence}
                              />
                            ))
                          ) : (
                            <span className="opacity-50 text-xs">No tags</span>
                          )}
                          {card.tags && card.tags.length > 5 && (
                            <span className="opacity-50 text-xs">+{card.tags.length - 5}</span>
                          )}
                        </div>
                      </td>
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
                    <td colSpan={6} className="text-center py-6">
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
