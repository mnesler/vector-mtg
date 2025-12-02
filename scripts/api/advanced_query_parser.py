#!/usr/bin/env python3
"""
Advanced Query Parser for MTG searches.
Handles complex queries with type filters, color filters, and numeric constraints.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ParsedQuery:
    """Structured representation of a parsed MTG search query."""
    positive_terms: str  # What to search FOR (e.g., "zombies")
    exclusions: List[str]  # Terms to EXCLUDE (e.g., ["black"])
    filters: Dict[str, Any]  # Structured filters (cmc, colors, types, etc.)
    original_query: str


class AdvancedQueryParser:
    """
    Parse complex MTG queries into structured filters.
    
    Supports:
    - Creature types: "zombies", "vampires", "dragons"
    - Color filters: "blue", "not black", "only red"
    - CMC filters: "more than 3 mana", "cmc < 4", "2 mana or less"
    - Type filters: "creatures", "instants", "artifacts"
    - Keyword filters: "with flying", "no haste"
    - Rarity filters: "rare", "mythic or rare"
    - Power/Toughness: "power > 4", "3/3 or bigger"
    """
    
    # MTG colors (case-insensitive)
    COLORS = ['white', 'blue', 'black', 'red', 'green', 'colorless']
    COLOR_ABBREV = {'w': 'white', 'u': 'blue', 'b': 'black', 'r': 'red', 'g': 'green'}
    COLOR_TO_SYMBOL = {'white': 'W', 'blue': 'U', 'black': 'B', 'red': 'R', 'green': 'G'}
    
    # Card types
    CARD_TYPES = ['creature', 'instant', 'sorcery', 'enchantment', 'artifact', 
                  'planeswalker', 'land', 'battle']
    
    # Common keywords
    KEYWORDS = ['flying', 'trample', 'haste', 'vigilance', 'deathtouch', 
                'lifelink', 'menace', 'reach', 'first strike', 'double strike',
                'hexproof', 'indestructible', 'flash', 'defender']
    
    # Rarities
    RARITIES = ['common', 'uncommon', 'rare', 'mythic', 'mythic rare']
    
    def __init__(self):
        """Initialize the parser with compiled regex patterns."""
        # Compile patterns for efficiency
        self.cmc_patterns = [
            # "more than X mana", "greater than X mana"
            (r'\b(?:more|greater)\s+than\s+(\d+)\s+(?:mana|cmc)', 'gt'),
            # "less than X mana", "fewer than X mana"
            (r'\b(?:less|fewer)\s+than\s+(\d+)\s+(?:mana|cmc)', 'lt'),
            # "X mana or more", "X+ mana"
            (r'\b(\d+)\s+(?:mana\s+)?or\s+more', 'gte'),
            (r'\b(\d+)\+\s*mana', 'gte'),
            # "X mana or less", "X- mana"
            (r'\b(\d+)\s+(?:mana\s+)?or\s+less', 'lte'),
            (r'\b(\d+)\-\s*mana', 'lte'),
            # "exactly X mana"
            (r'\bexactly\s+(\d+)\s+(?:mana|cmc)', 'eq'),
            # "X mana" (defaults to exact match)
            (r'\b(\d+)\s+mana\b', 'eq'),
            # "cmc > X", "cmc >= X", etc.
            (r'\bcmc\s*([><=]+)\s*(\d+)', 'operator'),
        ]
        
        self.power_toughness_patterns = [
            # "power > X", "power >= X"
            (r'\bpower\s*([><=]+)\s*(\d+)', 'power'),
            # "toughness > X"
            (r'\btoughness\s*([><=]+)\s*(\d+)', 'toughness'),
            # "X/Y or bigger", "X/Y+"
            (r'\b(\d+)/(\d+)\s*(?:or\s+)?(?:bigger|larger|\+)', 'pt_gte'),
            # "X/Y or smaller", "X/Y-"
            (r'\b(\d+)/(\d+)\s*(?:or\s+)?(?:smaller|\-)', 'pt_lte'),
        ]
    
    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into structured filters.
        
        Args:
            query: Natural language search query
            
        Returns:
            ParsedQuery object with structured filters
            
        Examples:
            >>> parser.parse("zombies but not black more than 3 mana")
            ParsedQuery(
                positive_terms="zombies",
                exclusions=["black"],
                filters={
                    "type_line_contains": ["zombie"],
                    "cmc_gt": 3,
                    "exclude_colors": ["B"]
                }
            )
        """
        filters = {}
        exclusions = []
        query_cleaned = query.lower()
        
        # 1. Extract CMC filters
        cmc_filter = self._extract_cmc_filter(query_cleaned)
        if cmc_filter:
            filters.update(cmc_filter)
            # Remove CMC expressions from query
            query_cleaned = self._remove_cmc_expressions(query_cleaned)
        
        # 2. Extract power/toughness filters
        pt_filter = self._extract_power_toughness_filter(query_cleaned)
        if pt_filter:
            filters.update(pt_filter)
            query_cleaned = self._remove_pt_expressions(query_cleaned)
        
        # 3. Extract color filters (including exclusions)
        color_info = self._extract_color_filters(query_cleaned)
        if color_info.get('include_colors'):
            filters['include_colors'] = color_info['include_colors']
        if color_info.get('exclude_colors'):
            filters['exclude_colors'] = color_info['exclude_colors']
            exclusions.extend([c.lower() for c in color_info.get('exclude_color_names', [])])
        if color_info.get('only_colors'):
            filters['only_colors'] = color_info['only_colors']
        
        # Remove color expressions from query
        query_cleaned = color_info.get('cleaned_query', query_cleaned)
        
        # 4. Extract card type filters
        type_filter = self._extract_type_filter(query_cleaned)
        if type_filter:
            filters.update(type_filter)
            query_cleaned = self._remove_type_expressions(query_cleaned)
        
        # 5. Extract rarity filter
        rarity_filter = self._extract_rarity_filter(query_cleaned)
        if rarity_filter:
            filters['rarity'] = rarity_filter
            query_cleaned = self._remove_rarity_expressions(query_cleaned)
        
        # 6. Extract keyword filters
        keyword_info = self._extract_keyword_filters(query_cleaned)
        if keyword_info.get('include_keywords'):
            filters['include_keywords'] = keyword_info['include_keywords']
        if keyword_info.get('exclude_keywords'):
            filters['exclude_keywords'] = keyword_info['exclude_keywords']
            exclusions.extend(keyword_info['exclude_keywords'])
        query_cleaned = keyword_info.get('cleaned_query', query_cleaned)
        
        # 7. Clean up remaining query as positive search terms
        positive_terms = re.sub(r'\s+', ' ', query_cleaned).strip()
        positive_terms = re.sub(r'[,;]+', ' ', positive_terms).strip()
        positive_terms = positive_terms.replace('but', '').strip()
        
        return ParsedQuery(
            positive_terms=positive_terms,
            exclusions=list(set(exclusions)),  # Deduplicate
            filters=filters,
            original_query=query
        )
    
    def _extract_cmc_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract CMC/mana cost filters from query."""
        for pattern, op_type in self.cmc_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if op_type == 'operator':
                    # Handle "cmc > 3" style
                    operator = match.group(1)
                    value = int(match.group(2))
                    if operator == '>':
                        return {'cmc_gt': value}
                    elif operator == '>=':
                        return {'cmc_gte': value}
                    elif operator == '<':
                        return {'cmc_lt': value}
                    elif operator == '<=':
                        return {'cmc_lte': value}
                    elif operator in ('=', '=='):
                        return {'cmc_eq': value}
                else:
                    value = int(match.group(1))
                    if op_type == 'gt':
                        return {'cmc_gt': value}
                    elif op_type == 'lt':
                        return {'cmc_lt': value}
                    elif op_type == 'gte':
                        return {'cmc_gte': value}
                    elif op_type == 'lte':
                        return {'cmc_lte': value}
                    elif op_type == 'eq':
                        return {'cmc_eq': value}
        return None
    
    def _remove_cmc_expressions(self, query: str) -> str:
        """Remove CMC expressions from query string."""
        for pattern, _ in self.cmc_patterns:
            query = re.sub(pattern, ' ', query, flags=re.IGNORECASE)
        return query
    
    def _extract_power_toughness_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract power/toughness filters."""
        result = {}
        for pattern, filter_type in self.power_toughness_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if filter_type == 'power':
                    operator = match.group(1)
                    value = int(match.group(2))
                    result[f'power_{self._op_to_suffix(operator)}'] = value
                elif filter_type == 'toughness':
                    operator = match.group(1)
                    value = int(match.group(2))
                    result[f'toughness_{self._op_to_suffix(operator)}'] = value
                elif filter_type == 'pt_gte':
                    result['power_gte'] = int(match.group(1))
                    result['toughness_gte'] = int(match.group(2))
                elif filter_type == 'pt_lte':
                    result['power_lte'] = int(match.group(1))
                    result['toughness_lte'] = int(match.group(2))
        return result if result else None
    
    def _op_to_suffix(self, operator: str) -> str:
        """Convert operator to filter suffix."""
        mapping = {
            '>': 'gt', '>=': 'gte', '<': 'lt', '<=': 'lte', '=': 'eq', '==': 'eq'
        }
        return mapping.get(operator, 'eq')
    
    def _remove_pt_expressions(self, query: str) -> str:
        """Remove power/toughness expressions from query."""
        for pattern, _ in self.power_toughness_patterns:
            query = re.sub(pattern, ' ', query, flags=re.IGNORECASE)
        return query
    
    def _extract_color_filters(self, query: str) -> Dict[str, Any]:
        """
        Extract color filters including exclusions and "only" constraints.
        
        Handles:
        - "blue zombies" -> include blue
        - "not black" -> exclude black
        - "only red" or "but only red" -> only red (exclude W,U,B,G)
        """
        include_colors = []
        exclude_colors = []
        exclude_color_names = []
        only_colors = []
        cleaned = query
        
        # Track which colors are explicitly excluded to avoid conflicts
        explicitly_excluded = set()
        
        # Pattern: "only X" or "but only X"
        only_pattern = r'(?:but\s+)?only\s+(' + '|'.join(self.COLORS) + r')'
        only_match = re.search(only_pattern, query, re.IGNORECASE)
        if only_match:
            color = only_match.group(1).lower()
            if color in self.COLOR_TO_SYMBOL:
                only_colors.append(self.COLOR_TO_SYMBOL[color])
                # Exclude all other colors
                for c, symbol in self.COLOR_TO_SYMBOL.items():
                    if c != color:
                        exclude_colors.append(symbol)
                        exclude_color_names.append(c)
                        explicitly_excluded.add(c)
            cleaned = re.sub(only_pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Pattern: "not X", "no X", "without X", "but not X"
        for color in self.COLORS:
            # Exclusion patterns
            excl_pattern = rf'\b(?:but\s+)?(?:not|no|without)\s+{color}\b'
            if re.search(excl_pattern, query, re.IGNORECASE):
                if color in self.COLOR_TO_SYMBOL:
                    exclude_colors.append(self.COLOR_TO_SYMBOL[color])
                    exclude_color_names.append(color)
                    explicitly_excluded.add(color)
                cleaned = re.sub(excl_pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Inclusion patterns (just color name without negation)
        # Only if not already in "only" clause AND not explicitly excluded
        if not only_colors:
            for color in self.COLORS:
                # Skip if this color was explicitly excluded
                if color in explicitly_excluded:
                    continue
                    
                incl_pattern = rf'\b{color}\b(?!\s+(?:not|no|without))'
                if re.search(incl_pattern, query, re.IGNORECASE):
                    if color in self.COLOR_TO_SYMBOL:
                        include_colors.append(self.COLOR_TO_SYMBOL[color])
        
        return {
            'include_colors': include_colors if include_colors else None,
            'exclude_colors': exclude_colors if exclude_colors else None,
            'exclude_color_names': exclude_color_names,
            'only_colors': only_colors if only_colors else None,
            'cleaned_query': cleaned
        }
    
    def _extract_type_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract card type filters."""
        types_found = []
        for card_type in self.CARD_TYPES:
            # Match plural forms too (creatures, artifacts, etc.)
            pattern = rf'\b{card_type}s?\b'
            if re.search(pattern, query, re.IGNORECASE):
                types_found.append(card_type)
        
        if types_found:
            return {'type_line_contains': types_found}
        return None
    
    def _remove_type_expressions(self, query: str) -> str:
        """Remove card type expressions from query."""
        for card_type in self.CARD_TYPES:
            query = re.sub(rf'\b{card_type}s?\b', ' ', query, flags=re.IGNORECASE)
        return query
    
    def _extract_rarity_filter(self, query: str) -> Optional[str]:
        """Extract rarity filter."""
        for rarity in self.RARITIES:
            if re.search(rf'\b{rarity}\b', query, re.IGNORECASE):
                return rarity.replace(' ', '')  # "mythic rare" -> "mythicrare"
        return None
    
    def _remove_rarity_expressions(self, query: str) -> str:
        """Remove rarity expressions from query."""
        for rarity in self.RARITIES:
            query = re.sub(rf'\b{rarity}\b', ' ', query, flags=re.IGNORECASE)
        return query
    
    def _extract_keyword_filters(self, query: str) -> Dict[str, Any]:
        """Extract keyword ability filters."""
        include_keywords = []
        exclude_keywords = []
        cleaned = query
        
        for keyword in self.KEYWORDS:
            # With/has keyword
            with_pattern = rf'\b(?:with|has|having)\s+{keyword}\b'
            if re.search(with_pattern, query, re.IGNORECASE):
                include_keywords.append(keyword)
                cleaned = re.sub(with_pattern, ' ', cleaned, flags=re.IGNORECASE)
            
            # Without/no keyword
            without_pattern = rf'\b(?:without|no)\s+{keyword}\b'
            if re.search(without_pattern, query, re.IGNORECASE):
                exclude_keywords.append(keyword)
                cleaned = re.sub(without_pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        return {
            'include_keywords': include_keywords if include_keywords else None,
            'exclude_keywords': exclude_keywords if exclude_keywords else None,
            'cleaned_query': cleaned
        }
    
    def to_sql_where_clause(self, parsed: ParsedQuery) -> tuple[str, List[Any]]:
        """
        Convert parsed query to SQL WHERE clause and parameters.
        
        Returns:
            Tuple of (where_clause_string, list_of_parameters)
        """
        conditions = []
        params = []
        
        # CMC filters
        if 'cmc_gt' in parsed.filters:
            conditions.append("cmc > %s")
            params.append(parsed.filters['cmc_gt'])
        if 'cmc_gte' in parsed.filters:
            conditions.append("cmc >= %s")
            params.append(parsed.filters['cmc_gte'])
        if 'cmc_lt' in parsed.filters:
            conditions.append("cmc < %s")
            params.append(parsed.filters['cmc_lt'])
        if 'cmc_lte' in parsed.filters:
            conditions.append("cmc <= %s")
            params.append(parsed.filters['cmc_lte'])
        if 'cmc_eq' in parsed.filters:
            conditions.append("cmc = %s")
            params.append(parsed.filters['cmc_eq'])
        
        # Color filters
        if 'exclude_colors' in parsed.filters:
            for color_symbol in parsed.filters['exclude_colors']:
                conditions.append("(mana_cost NOT LIKE %s OR mana_cost IS NULL)")
                params.append(f'%{{{color_symbol}}}%')
        
        if 'include_colors' in parsed.filters:
            color_conditions = []
            for color_symbol in parsed.filters['include_colors']:
                color_conditions.append("mana_cost LIKE %s")
                params.append(f'%{{{color_symbol}}}%')
            if color_conditions:
                conditions.append(f"({' OR '.join(color_conditions)})")
        
        if 'only_colors' in parsed.filters:
            # Must contain only these colors
            for color_symbol in parsed.filters['only_colors']:
                conditions.append("mana_cost LIKE %s")
                params.append(f'%{{{color_symbol}}}%')
        
        # Type filters
        if 'type_line_contains' in parsed.filters:
            type_conditions = []
            for card_type in parsed.filters['type_line_contains']:
                type_conditions.append("type_line ILIKE %s")
                params.append(f'%{card_type}%')
            if type_conditions:
                conditions.append(f"({' OR '.join(type_conditions)})")
        
        # Rarity filter
        if 'rarity' in parsed.filters:
            conditions.append("rarity = %s")
            params.append(parsed.filters['rarity'])
        
        # Keyword filters
        if 'include_keywords' in parsed.filters:
            for keyword in parsed.filters['include_keywords']:
                conditions.append("(keywords @> ARRAY[%s]::text[] OR oracle_text ILIKE %s)")
                params.extend([keyword, f'%{keyword}%'])
        
        if 'exclude_keywords' in parsed.filters:
            for keyword in parsed.filters['exclude_keywords']:
                conditions.append("NOT (keywords @> ARRAY[%s]::text[] OR oracle_text ILIKE %s)")
                params.extend([keyword, f'%{keyword}%'])
        
        # Power/Toughness filters
        for key in ['power_gt', 'power_gte', 'power_lt', 'power_lte', 'power_eq']:
            if key in parsed.filters:
                op = key.split('_')[1]
                op_sql = {'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=', 'eq': '='}[op]
                conditions.append(f"CAST(power AS INTEGER) {op_sql} %s")
                params.append(parsed.filters[key])
        
        for key in ['toughness_gt', 'toughness_gte', 'toughness_lt', 'toughness_lte', 'toughness_eq']:
            if key in parsed.filters:
                op = key.split('_')[1]
                op_sql = {'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=', 'eq': '='}[op]
                conditions.append(f"CAST(toughness AS INTEGER) {op_sql} %s")
                params.append(parsed.filters[key])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        return where_clause, params


# Singleton instance
_parser_instance = None


def get_advanced_parser() -> AdvancedQueryParser:
    """Get or create the global advanced parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = AdvancedQueryParser()
    return _parser_instance
