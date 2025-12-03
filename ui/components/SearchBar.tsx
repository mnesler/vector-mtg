'use client';

import { useState, useEffect, useRef } from 'react';
import { computePosition, autoUpdate, offset, shift, flip } from '@floating-ui/dom';

type SearchMode = 'keyword' | 'semantic';

interface SearchBarProps {
  placeholder?: string;
  className?: string;
  onSearchResults?: (results: any[], query: string, mode: 'keyword' | 'semantic', hasMore: boolean) => void;
  onSearchStart?: () => void;
}

export default function SearchBar({
  placeholder = "Search cards...",
  className = "",
  onSearchResults,
  onSearchStart
}: SearchBarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<SearchMode>('semantic');
  const [isSearching, setIsSearching] = useState(false);
  const [showSemanticTooltip, setShowSemanticTooltip] = useState(false);
  const [showKeywordTooltip, setShowKeywordTooltip] = useState(false);

  const semanticBtnRef = useRef<HTMLButtonElement>(null);
  const keywordBtnRef = useRef<HTMLButtonElement>(null);
  const semanticTooltipRef = useRef<HTMLDivElement>(null);
  const keywordTooltipRef = useRef<HTMLDivElement>(null);

  const performSearch = async (query: string, mode: SearchMode) => {
    if (!query.trim()) {
      onSearchResults?.([], '', mode, false);
      return;
    }

    onSearchStart?.();
    setIsSearching(true);
    try {
      const endpoint = mode === 'keyword'
        ? `/api/cards/keyword?query=${encodeURIComponent(query)}&limit=10`
        : `/api/cards/hybrid?query=${encodeURIComponent(query)}&limit=10&threshold=0.50`;

      const response = await fetch(`http://localhost:8000${endpoint}`);

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      onSearchResults?.(data.cards || [], query, mode, data.has_more || false);
    } catch (error) {
      console.error('Search error:', error);
      onSearchResults?.([], query, mode, false);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    // Only auto-search for keyword mode
    if (searchMode === 'keyword') {
      const debounceTimer = setTimeout(() => {
        if (searchQuery.trim()) {
          performSearch(searchQuery, searchMode);
        } else {
          onSearchResults?.([], '', searchMode, false);
          setIsSearching(false);
        }
      }, 300);

      return () => clearTimeout(debounceTimer);
    } else {
      // For semantic mode, clear results when query is empty
      if (!searchQuery.trim()) {
        onSearchResults?.([], '', searchMode, false);
        setIsSearching(false);
      }
    }
  }, [searchQuery, searchMode]);

  useEffect(() => {
    if (showSemanticTooltip && semanticBtnRef.current && semanticTooltipRef.current) {
      const cleanup = autoUpdate(semanticBtnRef.current, semanticTooltipRef.current, () => {
        computePosition(semanticBtnRef.current!, semanticTooltipRef.current!, {
          placement: 'bottom',
          middleware: [offset(8), flip(), shift({ padding: 8 })],
        }).then(({ x, y }) => {
          Object.assign(semanticTooltipRef.current!.style, {
            left: `${x}px`,
            top: `${y}px`,
          });
        });
      });
      return cleanup;
    }
  }, [showSemanticTooltip]);

  useEffect(() => {
    if (showKeywordTooltip && keywordBtnRef.current && keywordTooltipRef.current) {
      const cleanup = autoUpdate(keywordBtnRef.current, keywordTooltipRef.current, () => {
        computePosition(keywordBtnRef.current!, keywordTooltipRef.current!, {
          placement: 'bottom',
          middleware: [offset(8), flip(), shift({ padding: 8 })],
        }).then(({ x, y }) => {
          Object.assign(keywordTooltipRef.current!.style, {
            left: `${x}px`,
            top: `${y}px`,
          });
        });
      });
      return cleanup;
    }
  }, [showKeywordTooltip]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    
    // Clear results when input is cleared
    if (!value.trim()) {
      onSearchResults?.([], '', searchMode, false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchMode === 'semantic') {
      if (searchQuery.trim()) {
        performSearch(searchQuery, searchMode);
      } else {
        onSearchResults?.([], '', searchMode, false);
        setIsSearching(false);
      }
    }
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <div className="flex items-center justify-center gap-3">
        <div className="relative flex-1">
          <input
            type="search"
            placeholder={placeholder}
            value={searchQuery}
            onChange={handleSearchChange}
            onKeyPress={handleKeyPress}
            className="input variant-form-material w-full px-4 py-3 pr-24 rounded-lg"
            aria-label="Search cards"
            disabled={isSearching}
          />
          
          {/* Toggle Switch inside Search Bar */}
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1 bg-transparent">
            <button
              ref={semanticBtnRef}
              type="button"
              onClick={() => setSearchMode('semantic')}
              onMouseEnter={() => setShowSemanticTooltip(true)}
              onMouseLeave={() => setShowSemanticTooltip(false)}
              className={`btn btn-icon btn-sm transition-all ${
                searchMode === 'semantic'
                  ? 'variant-filled-primary shadow-lg scale-110'
                  : 'bg-transparent hover:variant-soft-surface opacity-50'
              }`}
              aria-label="Semantic search"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8.75 6.5L3.25 12l5.5 5.5m6.5-11l5.5 5.5l-5.5 5.5"/>
              </svg>
            </button>
            
            <button
              ref={keywordBtnRef}
              type="button"
              onClick={() => setSearchMode('keyword')}
              onMouseEnter={() => setShowKeywordTooltip(true)}
              onMouseLeave={() => setShowKeywordTooltip(false)}
              className={`btn btn-icon btn-sm transition-all ${
                searchMode === 'keyword'
                  ? 'variant-filled-primary shadow-lg scale-110'
                  : 'bg-transparent hover:variant-soft-surface opacity-50'
              }`}
              aria-label="Keyword search"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
            </button>
          </div>

          {isSearching && (
            <div className="absolute right-24 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin h-5 w-5 border-2 border-surface-500 border-t-primary-500 rounded-full"></div>
            </div>
          )}
        </div>
      </div>

      {/* Tooltips */}
      <div 
        ref={semanticTooltipRef}
        className={`card variant-filled-primary p-2 text-sm z-50 fixed ${showSemanticTooltip ? '' : 'hidden'}`}
        style={{ width: 'max-content', maxWidth: '200px' }}
      >
        Natural language search using AI similarity
      </div>
      <div 
        ref={keywordTooltipRef}
        className={`card variant-filled-primary p-2 text-sm z-50 fixed ${showKeywordTooltip ? '' : 'hidden'}`}
        style={{ width: 'max-content', maxWidth: '200px' }}
      >
        Exact text matching in card names and abilities
      </div>
    </div>
  );
}
