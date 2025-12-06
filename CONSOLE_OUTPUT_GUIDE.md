# Enhanced Console Output - EDHREC Scraper

## What You'll See When Running

### Startup Phase

```
######################################################################
# EDHREC SMART SCRAPER TEST
# URL: https://edhrec.com/commanders/atraxa-praetors-voice
# Strategy: elements
# Headless: True
# Started: 2024-12-06 10:30:45
######################################################################

======================================================================
INITIALIZING BROWSER
======================================================================
✓ Found Chromium: /usr/bin/chromium-browser
  Mode: Headless (no visible window)
  Images: Disabled (faster)

Searching for chromedriver...
✓ Found chromedriver: /usr/bin/chromedriver

Starting Chromium browser...
✓ Browser started successfully
======================================================================
```

### Page Loading Phase

```
======================================================================
Loading: https://edhrec.com/commanders/atraxa-praetors-voice
Strategy: elements
======================================================================

Navigating to page...
✓ Page loaded successfully
Initializing content handler...
✓ Content handler ready

Waiting for initial content to load...
✓ Initial content ready
```

### Scrolling Phase (Real-time Updates)

```
======================================================================
Starting infinite scroll (checking every 300ms)...
======================================================================

[Scroll  1] Waiting for element count to stabilize... → 25 cards (+25 NEW) ✓
[Scroll  2] Waiting for element count to stabilize... → 50 cards (+25 NEW) ✓
[Scroll  3] Waiting for element count to stabilize... → 75 cards (+25 NEW) ✓
[Scroll  4] Waiting for element count to stabilize... → 100 cards (+25 NEW) ✓
[Scroll  5] Waiting for element count to stabilize... → 125 cards (+25 NEW) ✓
[Scroll  6] Waiting for element count to stabilize... → 150 cards (+25 NEW) ✓
[Scroll  7] Waiting for element count to stabilize... → 175 cards (+25 NEW) ✓
[Scroll  8] Waiting for element count to stabilize... → 200 cards (+25 NEW) ✓
[Scroll  9] Waiting for element count to stabilize... → 225 cards (+25 NEW) ✓
[Scroll 10] Waiting for element count to stabilize... → 245 cards (+20 NEW) ✓
[Scroll 11] Waiting for element count to stabilize... → 258 cards (+13 NEW) ✓
[Scroll 12] Waiting for element count to stabilize... → 265 cards (+7 NEW) ✓
[Scroll 13] Waiting for element count to stabilize... → 268 cards (+3 NEW) ✓
[Scroll 14] Waiting for element count to stabilize... → 268 cards (NO CHANGE #1/3)
[Scroll 15] Waiting for element count to stabilize... → 268 cards (NO CHANGE #2/3)
[Scroll 16] Waiting for element count to stabilize... → 268 cards (NO CHANGE #3/3)

======================================================================
✓ Scrolling complete: No new cards after 3 attempts
======================================================================
```

### Extraction Phase

```
======================================================================
Final count: 16 scrolls, 268 card elements found
======================================================================

Extracting card data from page...
Found 268 card elements to process
Processing cards.................... done
✓ Extracted 268 unique cards
```

### Results Display

```
====================================================================================================
CARD RESULTS (268 total cards, showing first 50)
====================================================================================================

#    Card Name                                     Synergy    Type                
---- --------------------------------------------- ---------- --------------------
1    Doubling Season                               32%        Enchantment         
2    Winding Constrictor                           28%        Creature            
3    Corpsejack Menace                             27%        Creature            
4    Vorinclex, Monstrous Raider                   26%        Creature            
5    Teferi, Temporal Pilgrim                      25%        Planeswalker        
...
50   Toxic Deluge                                  8%         Sorcery             

... and 218 more cards

====================================================================================================
```

### Summary Statistics

```
======================================================================
SUMMARY STATISTICS
======================================================================
  Total unique cards: 268
  Cards with synergy data: 245
  Cards with type data: 180
  Elapsed time: 12.3 seconds
  Average: 0.05 seconds per card

SAMPLE DATA (first 3 cards):
  1. Doubling Season
     URL: https://edhrec.com/cards/doubling-season
     Synergy: 32%
     Type: Enchantment
  
  2. Winding Constrictor
     URL: https://edhrec.com/cards/winding-constrictor
     Synergy: 28%
     Type: Creature
  
  3. Corpsejack Menace
     URL: https://edhrec.com/cards/corpsejack-menace
     Synergy: 27%
     Type: Creature

======================================================================
✓ SCRAPING COMPLETED SUCCESSFULLY
======================================================================

Cleaning up...
✓ Browser closed successfully
```

## Error Reporting Examples

### Browser Initialization Error

```
======================================================================
INITIALIZING BROWSER
======================================================================
✗ ERROR: Chromium not found at /usr/bin/chromium-browser
  Install with: sudo apt-get install chromium-browser

✗ FAILED: Could not initialize browser
```

### Chromedriver Not Found

```
Searching for chromedriver...
✗ ERROR: chromedriver not found!

Tried these locations:
  - /usr/bin/chromedriver
  - /usr/local/bin/chromedriver
  - /snap/bin/chromium.chromedriver
  - chromedriver

Install with: sudo apt-get install chromium-chromedriver
```

### Scroll Error (Non-Fatal)

```
[Scroll  5] Waiting for element count to stabilize... 
⚠ WARNING: Content detection error on scroll 5: StaleElementReferenceException
  Attempting to count cards anyway...
→ 125 cards (+25 NEW) ✓
```

### Extraction Errors

```
Processing cards.................... done
✓ Extracted 268 unique cards
⚠ 12 extraction errors (non-critical)
```

### Network Error

```
Navigating to page...
✗ ERROR loading page: TimeoutException: Timeout waiting for page load

✗ UNEXPECTED ERROR: TimeoutException
  Error type: TimeoutException
  Full traceback:
  [detailed stack trace]
```

## Progress Indicators

### Dots During Extraction

```
Processing cards....................  (shows progress, 1 dot per 5%)
```

### Real-time Scroll Updates

Each scroll shows:
- **Scroll number** - `[Scroll 14]`
- **Action** - What strategy is being used
- **Result arrow** - `→`
- **Card count** - Current total
- **Change** - `(+25 NEW)` or `(NO CHANGE #2/3)`
- **Status** - `✓` for success

### Completion Markers

- `✓` - Success
- `✗` - Error (fatal)
- `⚠` - Warning (non-fatal)

## Verbosity Levels

The script provides **detailed output by default**:

1. ✅ **Startup checks** - Browser found, driver found
2. ✅ **Configuration** - Headless mode, images disabled
3. ✅ **Page loading** - URL, load status
4. ✅ **Every scroll** - Card count changes in real-time
5. ✅ **Extraction progress** - Dots showing progress
6. ✅ **Errors as they happen** - Immediate reporting
7. ✅ **Final statistics** - Time, cards, data completeness

## Sample Run Time

**Typical commander page (250-300 cards):**
- Browser startup: 2-3 seconds
- Page load: 1-2 seconds
- Scrolling: 5-8 seconds (15-20 scrolls)
- Extraction: 1-2 seconds
- **Total: 10-15 seconds**

## What to Look For

### Good Signs ✓
```
✓ Browser started successfully
✓ Page loaded successfully
+25 NEW, +25 NEW, +25 NEW  (cards loading consistently)
NO CHANGE #3/3  (proper completion detection)
✓ Extracted XXX unique cards
✓ SCRAPING COMPLETED SUCCESSFULLY
```

### Warning Signs ⚠
```
⚠ WARNING: Content detection error  (occasional is OK)
⚠ 12 extraction errors (non-critical)  (some extraction issues, but still successful)
```

### Problem Signs ✗
```
✗ ERROR: chromedriver not found  (needs installation)
✗ ERROR loading page  (network or site issue)
✗ Failed to count cards  (serious problem)
```

## Running the Enhanced Scraper

```bash
cd /home/maxwell/vector-mtg
python scripts/test_chromium_scraper.py --strategy=elements
```

All output goes to console in real-time, so you can monitor progress and catch errors immediately!
