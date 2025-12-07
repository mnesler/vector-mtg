#!/usr/bin/env python3
"""
Enhanced EDHREC Combo Scraper v2.0
Extracts detailed combo data from EDHREC category pages with:
- Individual category page scraping
- Comprehensive data extraction (all fields)
- File-based rate limiting
- Checkpoint/resume functionality
- Data validation with alerts
- Progress tracking with tqdm
"""

from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time
import re
import os
import argparse
import logging
from tqdm import tqdm
import requests
from urllib.parse import quote

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

CATEGORY_SLUGS = {
    "Mono-White": "mono-white",
    "Mono-Blue": "mono-blue",
    "Mono-Black": "mono-black",
    "Mono-Red": "mono-red",
    "Mono-Green": "mono-green",
    "Azorius": "azorius",
    "Dimir": "dimir",
    "Rakdos": "rakdos",
    "Gruul": "gruul",
    "Selesnya": "selesnya",
    "Orzhov": "orzhov",
    "Izzet": "izzet",
    "Golgari": "golgari",
    "Boros": "boros",
    "Simic": "simic",
    "Naya": "naya",
    "Bant": "bant",
    "Abzan": "abzan",
    "Sultai": "sultai",
    "Five-Color": "five-color",
    "Colorless": "colorless",
    "Esper": "esper",
    "Grixis": "grixis",
    "Jund": "jund",
    "Jeskai": "jeskai",
    "Mardu": "mardu",
    "Temur": "temur",
    "Yore-Tiller": "yore-tiller",
    "Glint-Eye": "glint-eye",
    "Dune-Brood": "dune-brood",
    "Ink-Treader": "ink-treader",
    "Witch-Maw": "witch-maw"
}

RATE_LIMIT_FILE = "edhrec_rate_limit.json"
CHECKPOINT_FILE = "edhrec_scraper_checkpoint.json"

# Global logger - initialize with basic config
logger = logging.getLogger("edhrec_scraper")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console_handler)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_logger(output_dir):
    """Configure logging to file and console"""
    global logger
    
    log_file = os.path.join(output_dir, "_errors.log")
    
    # Create logger
    logger = logging.getLogger("edhrec_scraper")
    logger.setLevel(logging.INFO)
    
    # File handler (JSON lines format)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def wait_for_rate_limit(delay_seconds=2.0):
    """
    Enforce minimum delay between requests using file-based tracking.
    """
    if not os.path.exists(RATE_LIMIT_FILE):
        # First request
        rate_data = {
            'last_request_time': datetime.now().isoformat(),
            'requests_count': 1,
            'session_start': datetime.now().isoformat()
        }
        with open(RATE_LIMIT_FILE, 'w') as f:
            json.dump(rate_data, f, indent=2)
        return
    
    # Load last request time
    with open(RATE_LIMIT_FILE, 'r') as f:
        data = json.load(f)
    
    last_time = datetime.fromisoformat(data['last_request_time'])
    elapsed = (datetime.now() - last_time).total_seconds()
    
    if elapsed < delay_seconds:
        wait_time = delay_seconds - elapsed
        time.sleep(wait_time)
    
    # Update rate limit file
    rate_data = {
        'last_request_time': datetime.now().isoformat(),
        'requests_count': data.get('requests_count', 0) + 1,
        'session_start': data.get('session_start', datetime.now().isoformat())
    }
    
    with open(RATE_LIMIT_FILE, 'w') as f:
        json.dump(rate_data, f, indent=2)


# ============================================================================
# CHECKPOINT SYSTEM
# ============================================================================

def create_new_checkpoint(categories, config):
    """Create new checkpoint for scraping session"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = config.get('output_dir') or f"edhrec_combos_detailed_{timestamp}"
    
    checkpoint = {
        'session_id': f"scrape_{timestamp}",
        'started_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'total_categories': len(categories),
        'completed_categories': [],
        'failed_categories': [],
        'pending_categories': list(categories),
        'output_directory': output_dir,
        'validation_warnings': [],
        'config': config
    }
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    return checkpoint


def load_checkpoint():
    """Load existing checkpoint if available"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)
            logger.info(f"📂 Resuming session: {checkpoint['session_id']}")
            logger.info(f"   Completed: {len(checkpoint['completed_categories'])}/{checkpoint['total_categories']}")
            return checkpoint
    return None


def save_checkpoint(checkpoint):
    """Save checkpoint to file"""
    checkpoint['last_updated'] = datetime.now().isoformat()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


# ============================================================================
# DATA EXTRACTION
# ============================================================================

# Global card cache to avoid duplicate API calls across combos
CARD_CACHE = {}

def slugify_card_name(name):
    """Convert card name to EDHREC URL slug format"""
    # Clean the name first
    cleaned = clean_card_name(name)
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = cleaned.lower()
    # Replace special characters
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def fetch_card_details(card_name, delay_seconds=2.0, use_cache=True):
    """
    Fetch detailed card data from EDHREC API with caching.
    Returns full card object or None if fetch fails.
    
    Args:
        card_name: Name of the card to fetch
        delay_seconds: Rate limit delay
        use_cache: If True, use cached data if available
    """
    # Check cache first
    if use_cache and card_name in CARD_CACHE:
        logger.debug(f"   💾 Using cached data: {card_name}")
        return CARD_CACHE[card_name]
    
    slug = slugify_card_name(card_name)
    url = f"https://json.edhrec.com/cards/{slug}"
    
    try:
        # Respect rate limiting
        wait_for_rate_limit(delay_seconds)
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            card_data = response.json()
            logger.debug(f"   ✓ Fetched card details: {card_name}")
            
            # Cache the result
            if use_cache:
                CARD_CACHE[card_name] = card_data
            
            return card_data
        elif response.status_code == 404:
            logger.debug(f"   ⚠️  Card not found on EDHREC: {card_name}")
            
            # Cache negative result to avoid re-fetching
            if use_cache:
                CARD_CACHE[card_name] = None
            
            return None
        else:
            logger.warning(f"   ⚠️  Failed to fetch {card_name}: HTTP {response.status_code}")
            return None
            
    except requests.Timeout:
        logger.warning(f"   ⚠️  Timeout fetching card: {card_name}")
        return None
    except Exception as e:
        logger.warning(f"   ⚠️  Error fetching {card_name}: {e}")
        return None


def clean_card_name(name):
    """Remove prices and other artifacts from card names"""
    # Remove ALL price patterns (multiple prices like $23.99$18.65$16.99)
    name = re.sub(r'\$[\d.,]+', '', name)
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def extract_combo_data(combo_element, combo_index, fetch_card_data=True, delay_seconds=2.0):
    """
    Extract ALL available fields from a combo element.
    Handles missing/incomplete data gracefully.
    
    Args:
        combo_element: Playwright element containing combo
        combo_index: Sequential index of combo
        fetch_card_data: If True, fetch detailed card data from EDHREC API
        delay_seconds: Rate limit delay for API requests
    """
    combo_data = {
        'combo_id': f'combo_{combo_index:04d}',
        'cards': [],
        'card_count': 0,
        'results': [],
        'prerequisites': [],
        'steps': [],
        'color_identity': [],
        'tags': [],
        'raw_text': ''
    }
    
    try:
        # Extract all text content for analysis
        full_text = combo_element.text_content() or ""
        combo_data['raw_text'] = full_text[:500]  # Store first 500 chars for debugging
        
        # Extract card names - try multiple patterns
        # Look for links to card pages (most reliable)
        card_links = combo_element.query_selector_all('a[href*="/cards/"]')
        seen_cards = set()
        
        for card_elem in card_links:
            card_name = card_elem.text_content().strip()
            card_name = clean_card_name(card_name)  # Clean up prices
            if card_name and card_name not in seen_cards and len(card_name) > 2:
                seen_cards.add(card_name)
                
                # Create basic card object
                card_obj = {'name': card_name}
                
                # Fetch detailed data from EDHREC API if enabled
                if fetch_card_data:
                    try:
                        card_details = fetch_card_details(card_name, delay_seconds)
                        if card_details:
                            card_obj['details'] = card_details
                    except Exception as e:
                        logger.debug(f"   Error fetching card details for {card_name}: {e}")
                
                combo_data['cards'].append(card_obj)
        
        # If no cards found via links, try other selectors
        if not combo_data['cards']:
            # Try finding card names in any bold text or specific classes
            card_elements = combo_element.query_selector_all('strong, b, .card-name, [class*="card"]')
            for card_elem in card_elements:
                card_name = card_elem.text_content().strip()
                card_name = clean_card_name(card_name)  # Clean up prices
                # Filter out common non-card text
                if (card_name and card_name not in seen_cards and 
                    len(card_name) > 2 and len(card_name) < 100 and
                    not card_name.lower().startswith(('infinite', 'combo', 'result'))):
                    seen_cards.add(card_name)
                    
                    # Create basic card object
                    card_obj = {'name': card_name}
                    
                    # Fetch detailed data from EDHREC API if enabled
                    if fetch_card_data:
                        try:
                            card_details = fetch_card_details(card_name, delay_seconds)
                            if card_details:
                                card_obj['details'] = card_details
                        except Exception as e:
                            logger.debug(f"   Error fetching card details for {card_name}: {e}")
                    
                    combo_data['cards'].append(card_obj)
        
        combo_data['card_count'] = len(combo_data['cards'])
        
        # Extract results/outcomes - look for common patterns
        result_patterns = [
            r'Infinite (.+?)(?:\.|$|,)',
            r'(?:Win|Wins) the game',
            r'(?:Draw|Draws) (?:the|your) deck',
            r'(?:Mill|Mills) (?:each opponent|target player)',
            r'Near-infinite (.+?)(?:\.|$|,)',
        ]
        
        for pattern in result_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                result = match.strip()
                if result and result not in combo_data['results'] and len(result) > 3:
                    combo_data['results'].append(result)
        
        # Try to find result elements
        result_elems = combo_element.query_selector_all('[class*="result"], [class*="outcome"]')
        for elem in result_elems:
            result_text = elem.text_content().strip()
            if result_text and len(result_text) > 5 and result_text not in combo_data['results']:
                combo_data['results'].append(result_text)
        
        # Extract prerequisites - look for common patterns
        prereq_keywords = [
            'All permanents on the battlefield',
            'Mana available',
            'You control',
            'You have',
            'must be',
            'in play',
            'on the battlefield'
        ]
        
        for line in full_text.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in prereq_keywords):
                if line not in combo_data['prerequisites'] and len(line) > 10:
                    combo_data['prerequisites'].append(line)
        
        # Extract tags from text
        tag_keywords = ['infinite', 'draw', 'mana', 'damage', 'tokens', 'counters', 
                        'lifegain', 'mill', 'sacrifice', 'etb', 'death', 'trigger']
        for tag in tag_keywords:
            if tag in full_text.lower() and tag not in combo_data['tags']:
                combo_data['tags'].append(tag)
        
    except Exception as e:
        logger.warning(f"Error extracting combo {combo_index}: {e}")
    
    return combo_data


def scroll_and_load_all(page, target_count=None, max_scrolls=200, scroll_delay=2.0, smooth_scroll=False):
    """
    Scroll page to load all dynamic content.
    Also clicks "Load More" buttons if present.
    Stops when:
    1. No new content loads (page height doesn't change)
    2. Target combo count is reached (if specified)
    3. Max scrolls reached
    
    Args:
        page: Playwright page object
        target_count: Target number of combos to load (optional)
        max_scrolls: Maximum number of scroll attempts
        scroll_delay: Seconds to wait between scrolls/clicks
        smooth_scroll: If True, use smooth scrolling animation
    
    Returns tuple: (scroll_count, current_combo_count)
    """
    scroll_count = 0
    no_change_count = 0
    last_combo_count = 0
    
    logger.info(f"   🐌 Scroll settings: delay={scroll_delay}s, smooth={'yes' if smooth_scroll else 'no'}, max_scrolls={max_scrolls}")
    
    while scroll_count < max_scrolls:
        # Check current combo count
        current_combos = page.query_selector_all('.ComboView_cardContainer__x029o')
        current_combo_count = len(current_combos)
        
        # Log progress
        if scroll_count % 10 == 0 or scroll_count < 5:
            logger.info(f"   Scroll {scroll_count}: Found {current_combo_count} combos")
        
        # Check if we reached target (just for logging, keep going)
        if target_count and current_combo_count >= target_count:
            logger.info(f"   ✓ Reached target count: {current_combo_count}/{target_count} - continuing to load remaining combos...")
            # Don't break - keep going until button disappears
        
        # Look for "Load More" button - be very specific
        button_clicked = False
        try:
            # Try the most specific selector first
            load_more = page.query_selector('button:has-text("Load More")')
            if load_more and load_more.is_visible():
                button_text = load_more.text_content() or ""
                # Verify it's actually "Load More" and not CSS/HTML content
                if button_text.strip() == "Load More" or ("Load More" in button_text and len(button_text) < 50):
                    logger.info(f"   🔘 Clicking 'Load More' button (current count: {current_combo_count})")
                    
                    # Click and wait
                    load_more.click()
                    time.sleep(scroll_delay)  # Configurable wait
                    button_clicked = True
                    
                    # Verify the count actually increased
                    new_count = len(page.query_selector_all('.ComboView_cardContainer__x029o'))
                    if new_count <= current_combo_count:
                        logger.warning(f"   ⚠️  Button clicked but count didn't increase ({current_combo_count} -> {new_count})")
                        no_change_count += 1
                    else:
                        logger.info(f"   ✓ Count increased: {current_combo_count} -> {new_count}")
        except Exception as e:
            # Button might not exist anymore (all loaded)
            logger.debug(f"   Button check exception: {e}")
            pass
        
        # If button was clicked, don't count as no-change
        if button_clicked:
            no_change_count = 0
            scroll_count += 1
            continue
        
        # Check if count stopped increasing
        if current_combo_count == last_combo_count:
            no_change_count += 1
            if no_change_count >= 5:  # No change for 5 consecutive attempts (increased from 3)
                logger.info(f"   ✓ No new combos loading after {no_change_count} attempts (stabilized at {current_combo_count})")
                break
        else:
            no_change_count = 0
        
        last_combo_count = current_combo_count
        
        # Scroll down - choose smooth or instant
        if smooth_scroll:
            # Smooth scroll animation over 1 second
            page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
        else:
            # Instant jump
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        time.sleep(scroll_delay)  # Configurable wait for content to load
        
        scroll_count += 1
    
    # Final count
    final_combos = page.query_selector_all('.ComboView_cardContainer__x029o')
    final_count = len(final_combos)
    
    logger.info(f"   📊 Scrolling complete: {scroll_count} scrolls, {final_count} combos loaded")
    
    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)
    
    return scroll_count, final_count


def extract_all_combos(page, category, config):
    """Extract all combo data from loaded page with progressive saving"""
    combos = []
    
    # Use the specific EDHREC combo container class
    combo_selector = '.ComboView_cardContainer__x029o'
    combo_elements = page.query_selector_all(combo_selector)
    
    if not combo_elements:
        logger.warning(f"⚠️  No combo elements found for {category} using selector: {combo_selector}")
        return combos
    
    logger.info(f"   Found {len(combo_elements)} combo containers")
    
    # Get config settings
    fetch_card_data = config.get('fetch_card_data', True)
    delay_seconds = config.get('delay', 2.0)
    output_dir = config.get('output_directory')
    save_interval = 100  # Save every 100 combos
    
    if fetch_card_data:
        logger.info(f"   📥 Card data fetching: ENABLED (this will take time with {len(combo_elements)} combos)")
        logger.info(f"   ⏱️  Estimated time: ~{len(combo_elements) * 3 * delay_seconds / 60:.1f} minutes (assuming 3 cards per combo)")
        logger.info(f"   💾 Progressive saving: Every {save_interval} combos")
    else:
        logger.info(f"   📥 Card data fetching: DISABLED (fast mode)")
    
    # Progressive save file
    progress_file = None
    if output_dir:
        slug = CATEGORY_SLUGS.get(category, category.lower().replace(' ', '-'))
        progress_file = os.path.join(output_dir, f"{slug}_progress.json")
    
    # Extract data from each combo with progress bar
    with tqdm(total=len(combo_elements), 
              desc=f"   Extracting combos", 
              unit="combo",
              leave=False) as pbar:
        for idx, combo_elem in enumerate(combo_elements):
            try:
                combo_data = extract_combo_data(
                    combo_elem, 
                    idx + 1,
                    fetch_card_data=fetch_card_data,
                    delay_seconds=delay_seconds
                )
                combos.append(combo_data)  # Include all combos, even if cards list is empty
                pbar.update(1)
                
                # Progressive save every N combos
                if progress_file and (idx + 1) % save_interval == 0:
                    cache_size = len(CARD_CACHE)
                    logger.info(f"   💾 Progress save: {idx + 1}/{len(combo_elements)} combos | Card cache: {cache_size} cards")
                    
                    # Save intermediate data
                    progress_data = {
                        'metadata': {
                            'category': category,
                            'status': 'in_progress',
                            'extracted_count': len(combos),
                            'total_count': len(combo_elements),
                            'last_saved': datetime.now().isoformat(),
                            'card_cache_size': cache_size
                        },
                        'combos': combos
                    }
                    with open(progress_file, 'w') as f:
                        json.dump(progress_data, f, indent=2)
                
                # Log every 100 combos with cache stats
                elif (idx + 1) % 100 == 0:
                    cache_size = len(CARD_CACHE)
                    logger.info(f"   Progress: {idx + 1}/{len(combo_elements)} combos extracted | Card cache: {cache_size} cards")
                    
            except Exception as e:
                logger.warning(f"Error extracting combo {idx + 1} in {category}: {e}")
                pbar.update(1)
    
    # Final save
    if progress_file:
        cache_size = len(CARD_CACHE)
        logger.info(f"   💾 Final save: {len(combos)}/{len(combo_elements)} combos | Card cache: {cache_size} cards")
        
        progress_data = {
            'metadata': {
                'category': category,
                'status': 'completed',
                'extracted_count': len(combos),
                'total_count': len(combo_elements),
                'completed_at': datetime.now().isoformat(),
                'card_cache_size': cache_size
            },
            'combos': combos
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    # Log final cache statistics
    cache_size = len(CARD_CACHE)
    logger.info(f"   ✓ Extracted {len(combos)} combos")
    if fetch_card_data:
        logger.info(f"   💾 Card cache: {cache_size} unique cards cached")
    
    return combos


# ============================================================================
# CATEGORY SCRAPING
# ============================================================================

def scrape_category_page(category, url_slug, browser, config):
    """
    Scrape individual category page.
    Returns category data with all combos.
    """
    url = f"https://edhrec.com/combos/{url_slug}"
    start_time = time.time()
    
    page = browser.new_page()
    
    # Block ads, analytics, and trackers to speed up loading
    def block_ads(route):
        blocked_domains = [
            'google-analytics.com',
            'analytics.google.com',
            'mediavine.com',
            'doubleclick.net',
            'googletagmanager.com',
            'criteo.com',
            'pubmatic.com',
            'btloader.com',
            'connatix.com',
            'adentifi.com',
            'yahoo.com/sync',
            'consentmanager.net',
            'grow.me',
            'nr-data.net'
        ]
        
        if any(domain in route.request.url for domain in blocked_domains):
            route.abort()
        else:
            route.continue_()
    
    page.route("**/*", block_ads)
    
    # Capture console messages from the browser (but only errors, not warnings)
    def handle_console_msg(msg):
        if msg.type == 'error':
            logger.error(f"   [BROWSER CONSOLE] {msg.type}: {msg.text}")
    
    def handle_page_error(error):
        logger.error(f"   [BROWSER ERROR] {error}")
    
    page.on("console", handle_console_msg)
    page.on("pageerror", handle_page_error)
    
    try:
        logger.info(f"   Loading {url}...")
        page.goto(url, wait_until='domcontentloaded', timeout=120000)  # Just wait for DOM, not full network idle
        time.sleep(5)  # Give JavaScript time to initialize
        
        # Get expected count for this category
        expected_count = config.get('expected_counts', {}).get(category)
        
        # Scroll to load all content
        logger.info(f"   Scrolling to load all combos (target: {expected_count})...")
        scroll_count, loaded_count = scroll_and_load_all(
            page, 
            target_count=expected_count,
            scroll_delay=config.get('scroll_delay', 2.0),
            smooth_scroll=config.get('smooth_scroll', False)
        )
        logger.info(f"   Completed {scroll_count} scrolls, loaded {loaded_count} combos")
        
        # Extract combo data
        logger.info(f"   Extracting combo data...")
        combos = extract_all_combos(page, category, config)
        
        duration = time.time() - start_time
        
        # Take screenshot if enabled
        screenshot_path = None
        if config.get('screenshots', False):
            screenshot_dir = os.path.join(config['output_directory'], 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{url_slug}.png")
            page.screenshot(path=screenshot_path)
            logger.info(f"   📸 Screenshot saved: {screenshot_path}")
        
        page.close()
        
        # Build category data structure
        category_data = {
            'metadata': {
                'category': category,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'expected_count': expected_count,
                'extracted_count': len(combos),
                'scrape_duration_seconds': round(duration, 2),
                'scroll_count': scroll_count,
                'combos_loaded': loaded_count,
                'success': True,
                'screenshot': screenshot_path,
                'errors': []
            },
            'combos': combos
        }
        
        return category_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping {category}: {e}")
        
        # Save error screenshot
        error_screenshot = os.path.join(
            config['output_directory'],
            f"ERROR_{url_slug}_{datetime.now().strftime('%H%M%S')}.png"
        )
        try:
            page.screenshot(path=error_screenshot)
            logger.error(f"   Error screenshot: {error_screenshot}")
        except:
            pass
        
        page.close()
        raise


def scrape_category_with_retry(category, url_slug, browser, config, max_retries=3):
    """
    Scrape category with retry logic.
    Returns category data or None on failure.
    """
    for attempt in range(max_retries):
        try:
            data = scrape_category_page(category, url_slug, browser, config)
            return data
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed for {category}: {e}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # Exponential backoff
                logger.info(f"   Retrying in {wait_time}s...")
                time.sleep(wait_time)
    
    logger.error(f"❌ Failed to scrape {category} after {max_retries} attempts")
    return None


# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_combo_count(category, data, checkpoint):
    """
    Validate extracted combo count against expected count.
    Alert if significant mismatch.
    """
    expected = data['metadata']['expected_count']
    extracted = data['metadata']['extracted_count']
    
    if expected is None:
        logger.warning(f"⚠️  {category}: No expected count for validation")
        return
    
    diff = abs(expected - extracted)
    diff_percent = (diff / expected * 100) if expected > 0 else 0
    
    if diff_percent > 20:
        logger.error(f"❌ {category}: CRITICAL - Expected {expected}, got {extracted} ({diff_percent:.1f}% diff)")
        checkpoint['validation_warnings'].append({
            'category': category,
            'expected': expected,
            'extracted': extracted,
            'difference': diff,
            'difference_percent': round(diff_percent, 1),
            'severity': 'critical'
        })
    elif diff_percent > 10:
        logger.warning(f"⚠️  {category}: Moderate mismatch - Expected {expected}, got {extracted} ({diff_percent:.1f}% diff)")
        checkpoint['validation_warnings'].append({
            'category': category,
            'expected': expected,
            'extracted': extracted,
            'difference': diff,
            'difference_percent': round(diff_percent, 1),
            'severity': 'moderate'
        })
    elif diff_percent > 5:
        logger.info(f"ℹ️  {category}: Minor mismatch - Expected {expected}, got {extracted} ({diff_percent:.1f}% diff)")
        checkpoint['validation_warnings'].append({
            'category': category,
            'expected': expected,
            'extracted': extracted,
            'difference': diff,
            'difference_percent': round(diff_percent, 1),
            'severity': 'minor'
        })
    else:
        logger.info(f"✅ {category}: Validated - {extracted}/{expected} combos ({diff_percent:.1f}% diff)")


# ============================================================================
# FILE MANAGEMENT
# ============================================================================

def save_category_file(data, output_dir, category):
    """Save category data to individual JSON file"""
    slug = CATEGORY_SLUGS[category]
    filename = os.path.join(output_dir, f"{slug}.json")
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"✅ Saved: {filename}")


def generate_summary_file(checkpoint, output_dir):
    """Generate summary file with all results"""
    summary = {
        'session': {
            'session_id': checkpoint['session_id'],
            'started_at': checkpoint['started_at'],
            'completed_at': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - datetime.fromisoformat(checkpoint['started_at'])).total_seconds()
        },
        'configuration': checkpoint['config'],
        'results': {
            'categories_total': checkpoint['total_categories'],
            'categories_completed': len(checkpoint['completed_categories']),
            'categories_failed': len(checkpoint['failed_categories']),
            'success_rate': len(checkpoint['completed_categories']) / checkpoint['total_categories'] if checkpoint['total_categories'] > 0 else 0
        },
        'validation': {
            'warnings_count': len(checkpoint['validation_warnings']),
            'critical_count': len([w for w in checkpoint['validation_warnings'] if w['severity'] == 'critical']),
            'moderate_count': len([w for w in checkpoint['validation_warnings'] if w['severity'] == 'moderate']),
            'minor_count': len([w for w in checkpoint['validation_warnings'] if w['severity'] == 'minor']),
            'warnings': checkpoint['validation_warnings']
        },
        'completed_categories': checkpoint['completed_categories'],
        'failed_categories': checkpoint['failed_categories']
    }
    
    filename = os.path.join(output_dir, '_summary.json')
    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"📄 Summary saved: {filename}")
    
    # Generate validation report
    generate_validation_report(checkpoint, output_dir)


def generate_validation_report(checkpoint, output_dir):
    """Generate human-readable validation report"""
    warnings = checkpoint.get('validation_warnings', [])
    
    report = ["=" * 80]
    report.append("DATA VALIDATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    if not warnings:
        report.append("✅ All categories validated successfully - no significant mismatches")
    else:
        critical = [w for w in warnings if w['severity'] == 'critical']
        moderate = [w for w in warnings if w['severity'] == 'moderate']
        minor = [w for w in warnings if w['severity'] == 'minor']
        
        if critical:
            report.append(f"❌ CRITICAL MISMATCHES ({len(critical)}):")
            for w in critical:
                report.append(f"  {w['category']}: Expected {w['expected']}, got {w['extracted']} ({w['difference_percent']:.1f}% diff)")
            report.append("")
        
        if moderate:
            report.append(f"⚠️  MODERATE MISMATCHES ({len(moderate)}):")
            for w in moderate:
                report.append(f"  {w['category']}: Expected {w['expected']}, got {w['extracted']} ({w['difference_percent']:.1f}% diff)")
            report.append("")
        
        if minor:
            report.append(f"ℹ️  MINOR MISMATCHES ({len(minor)}):")
            for w in minor:
                report.append(f"  {w['category']}: Expected {w['expected']}, got {w['extracted']} ({w['difference_percent']:.1f}% diff)")
            report.append("")
    
    report.append("=" * 80)
    
    filename = os.path.join(output_dir, '_validation_report.txt')
    with open(filename, 'w') as f:
        f.write('\n'.join(report))
    
    logger.info(f"📊 Validation report: {filename}")


# ============================================================================
# MAIN SCRAPING WORKFLOW
# ============================================================================

def scrape_summary_page():
    """
    Scrape main combos page to get expected counts.
    This is the existing functionality.
    """
    url = "https://edhrec.com/combos"
    
    print(f"Fetching data from {url}...")
    
    combo_data = {
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'total_combos': None,
        'combos_by_color': {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            # Scroll to load content
            for i in range(5):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(0.5)
            
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            # Extract total
            total_elements = page.query_selector_all('text=/\\d+.*combo/i')
            for element in total_elements:
                text = element.text_content() or ""
                numbers = re.findall(r'(\d+)', text)
                if numbers:
                    count = int(numbers[0])
                    if count > 100:
                        combo_data['total_combos'] = count
                        break
            
            # Extract color categories
            body_text = page.inner_text('body')
            
            # Pattern for K format
            pattern_k = r'([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s*([\d.]+)K\s*combos?'
            matches_k = re.findall(pattern_k, body_text, re.IGNORECASE)
            
            for color_name, count_str in matches_k:
                count = int(float(count_str) * 1000)
                if count > 0 and count < 100000:
                    combo_data['combos_by_color'][color_name] = count
            
            # Pattern for regular numbers
            pattern_num = r'([A-Z][a-z]+(?:-[A-Z][a-z]+)?)(\d+)\s*combos?'
            matches_num = re.findall(pattern_num, body_text)
            
            for color_name, count_str in matches_num:
                count = int(count_str)
                if count > 0 and count < 50000:
                    if color_name not in combo_data['combos_by_color']:
                        combo_data['combos_by_color'][color_name] = count
            
            browser.close()
            
        except Exception as e:
            print(f"Error scraping summary: {e}")
            browser.close()
    
    return combo_data


def scrape_all_categories(args):
    """
    Main workflow for scraping all categories with progress tracking.
    """
    # First, scrape summary page to get expected counts
    print("\n" + "=" * 80)
    print("EDHREC ENHANCED COMBO SCRAPER v2.0")
    print("=" * 80)
    print()
    
    summary_data = scrape_summary_page()
    expected_counts = summary_data['combos_by_color']
    
    print(f"\n✓ Found {len(expected_counts)} categories with expected counts")
    
    # Determine which categories to scrape
    if args.categories:
        # Specific categories
        category_slugs = [s.strip() for s in args.categories.split(',')]
        categories_to_scrape = []
        for slug in category_slugs:
            # Find category name from slug
            for name, cat_slug in CATEGORY_SLUGS.items():
                if cat_slug == slug:
                    categories_to_scrape.append(name)
                    break
    elif args.limit:
        # Limit to first N categories
        categories_to_scrape = list(CATEGORY_SLUGS.keys())[:args.limit]
    else:
        # All categories
        categories_to_scrape = list(CATEGORY_SLUGS.keys())
    
    print(f"Categories to scrape: {len(categories_to_scrape)}")
    
    # Create or load checkpoint
    if args.resume:
        checkpoint = load_checkpoint()
        if not checkpoint:
            print("No checkpoint found to resume from. Starting new session.")
            checkpoint = create_new_checkpoint(categories_to_scrape, {
                'delay_seconds': args.delay,
                'delay': args.delay,  # For backward compatibility
                'max_retries': args.max_retries,
                'screenshots': args.screenshots,
                'output_dir': args.output_dir,
                'expected_counts': expected_counts,
                'scroll_delay': args.scroll_delay,
                'smooth_scroll': args.scroll_smooth,
                'fetch_card_data': args.fetch_card_data
            })
    else:
        checkpoint = create_new_checkpoint(categories_to_scrape, {
            'delay_seconds': args.delay,
            'delay': args.delay,  # For backward compatibility
            'max_retries': args.max_retries,
            'screenshots': args.screenshots,
            'output_dir': args.output_dir,
            'expected_counts': expected_counts,
            'scroll_delay': args.scroll_delay,
            'smooth_scroll': args.scroll_smooth,
            'fetch_card_data': args.fetch_card_data
        })
    
    # Add output_directory to config for easy access in scraping functions
    checkpoint['config']['output_directory'] = checkpoint['output_directory']
    
    # Setup logging
    global logger
    logger = setup_logger(checkpoint['output_directory'])
    
    logger.info(f"Session: {checkpoint['session_id']}")
    logger.info(f"Output directory: {checkpoint['output_directory']}")
    
    # Scrape categories with progress bar
    pending = checkpoint['pending_categories']
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        with tqdm(total=len(categories_to_scrape), 
                  desc="Scraping Categories",
                  unit="category",
                  initial=len(checkpoint['completed_categories'])) as pbar:
            
            for category in pending[:]:  # Copy to avoid modification issues
                pbar.set_description(f"Scraping {category}")
                
                # Rate limiting
                wait_for_rate_limit(checkpoint['config']['delay_seconds'])
                
                # Scrape category
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping: {category}")
                logger.info(f"{'='*60}")
                
                data = scrape_category_with_retry(
                    category,
                    CATEGORY_SLUGS[category],
                    browser,
                    checkpoint['config'],
                    args.max_retries
                )
                
                if data:
                    # Save category file
                    save_category_file(data, checkpoint['output_directory'], category)
                    checkpoint['completed_categories'].append(category)
                    
                    # Validate data
                    validate_combo_count(category, data, checkpoint)
                else:
                    checkpoint['failed_categories'].append(category)
                
                # Update checkpoint
                checkpoint['pending_categories'].remove(category)
                save_checkpoint(checkpoint)
                
                pbar.update(1)
        
        browser.close()
    
    # Generate summary
    generate_summary_file(checkpoint, checkpoint['output_directory'])
    
    # Print final results
    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE")
    print("=" * 80)
    print(f"Completed: {len(checkpoint['completed_categories'])}/{len(categories_to_scrape)}")
    print(f"Failed: {len(checkpoint['failed_categories'])}")
    print(f"Output directory: {checkpoint['output_directory']}")
    print("=" * 80)
    
    # Clean up checkpoint if fully completed
    if len(checkpoint['pending_categories']) == 0:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        if os.path.exists(RATE_LIMIT_FILE):
            os.remove(RATE_LIMIT_FILE)
        print("✓ Session completed - checkpoint cleaned up")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Enhanced EDHREC Combo Scraper with detailed category extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape summary only (original behavior)
  python scrape_edhrec_combos_v2.py
  
  # Detailed scraping with all categories
  python scrape_edhrec_combos_v2.py --detailed
  
  # Test with first 3 categories
  python scrape_edhrec_combos_v2.py --detailed --limit=3
  
  # Specific categories only
  python scrape_edhrec_combos_v2.py --detailed --categories="mono-white,simic"
  
  # Resume interrupted session
  python scrape_edhrec_combos_v2.py --detailed --resume
  
  # With screenshots enabled
  python scrape_edhrec_combos_v2.py --detailed --screenshots
  
  # Slow scrolling (better for reliability)
  python scrape_edhrec_combos_v2.py --detailed --limit=1 --scroll-delay=4 --scroll-smooth
  
  # Very slow, careful scraping
  python scrape_edhrec_combos_v2.py --detailed --delay=3 --scroll-delay=5 --scroll-smooth
        """
    )
    
    parser.add_argument('--detailed', action='store_true',
                       help='Scrape individual category pages for detailed combo data')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='Limit to first N categories (for testing)')
    parser.add_argument('--categories', type=str, metavar='CAT1,CAT2',
                       help='Comma-separated category slugs to scrape')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint')
    parser.add_argument('--delay', type=float, default=2.0, metavar='SEC',
                       help='Delay between requests in seconds (default: 2.0)')
    parser.add_argument('--max-retries', type=int, default=3, metavar='N',
                       help='Maximum retry attempts per category (default: 3)')
    parser.add_argument('--screenshots', action='store_true',
                       help='Enable screenshot capture for each category')
    parser.add_argument('--output-dir', type=str, metavar='DIR',
                       help='Custom output directory')
    parser.add_argument('--scroll-delay', type=float, default=2.0, metavar='SEC',
                       help='Delay between scrolls/button clicks (default: 2.0, try 3-5 for slower)')
    parser.add_argument('--scroll-smooth', action='store_true',
                       help='Use smooth scrolling instead of instant jump (slower but more natural)')
    parser.add_argument('--fetch-card-data', dest='fetch_card_data', action='store_true',
                       help='Fetch detailed card data from EDHREC API for each card')
    parser.add_argument('--no-fetch-card-data', dest='fetch_card_data', action='store_false',
                       help='Skip fetching detailed card data (faster but less complete, DEFAULT)')
    parser.set_defaults(fetch_card_data=False)  # Default to False for speed
    
    return parser.parse_args()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.detailed:
        # Enhanced mode - scrape individual categories
        scrape_all_categories(args)
    else:
        # Simple mode - just scrape summary (original behavior)
        print("EDHREC Combo Scraper - Summary Mode")
        print("=" * 80)
        print()
        
        combo_data = scrape_summary_page()
        
        print("\nCategories found:")
        for category, count in sorted(combo_data['combos_by_color'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count:,}")
        
        print(f"\nTotal categories: {len(combo_data['combos_by_color'])}")
        print("\nUse --detailed flag to scrape individual category pages")
