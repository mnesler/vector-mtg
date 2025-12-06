#!/usr/bin/env python3
"""
EDHREC Scraper - Advanced Dynamic Content Handling

This version uses multiple strategies to detect when dynamic content
has finished loading, rather than relying on fixed time delays.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedDynamicContentHandler:
    """
    Advanced strategies for handling dynamic content loading.
    
    Implements multiple detection methods:
    1. Network activity monitoring
    2. DOM mutation observation
    3. Element count stabilization
    4. Loading indicator detection
    5. Fallback to height-based detection
    """
    
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
    
    # =========================================================================
    # STRATEGY 1: Network Activity Monitoring
    # =========================================================================
    
    def wait_for_network_idle(self, idle_time=0.5, max_wait=10):
        """
        Wait for network to be idle by monitoring performance logs.
        
        This is the BEST approach but requires Chrome DevTools Protocol.
        
        Args:
            idle_time: Seconds of no network activity to consider "idle"
            max_wait: Maximum seconds to wait
            
        Returns:
            True if network became idle, False if timeout
        """
        # Enable performance logging
        self.driver.execute_cdp_cmd('Network.enable', {})
        
        start_time = time.time()
        last_activity_time = start_time
        
        while time.time() - start_time < max_wait:
            # Get pending requests
            pending = self.driver.execute_script("""
                return window.performance.getEntriesByType('resource')
                    .filter(r => r.responseEnd === 0).length;
            """)
            
            if pending > 0:
                last_activity_time = time.time()
            elif time.time() - last_activity_time >= idle_time:
                # Network has been idle for idle_time seconds
                logger.debug(f"Network idle after {time.time() - start_time:.2f}s")
                return True
            
            time.sleep(0.1)  # Check every 100ms
        
        logger.warning(f"Network idle timeout after {max_wait}s")
        return False
    
    # =========================================================================
    # STRATEGY 2: DOM Mutation Observer (JavaScript-based)
    # =========================================================================
    
    def wait_for_dom_stable(self, stable_time=0.3, max_wait=10):
        """
        Wait for DOM to stop mutating using MutationObserver.
        
        This watches for changes to the page structure.
        
        Args:
            stable_time: Seconds without mutations to consider "stable"
            max_wait: Maximum seconds to wait
            
        Returns:
            True if DOM stabilized, False if timeout
        """
        # Inject mutation observer
        self.driver.execute_script("""
            window._mutationCount = 0;
            window._lastMutationTime = Date.now();
            
            const observer = new MutationObserver((mutations) => {
                window._mutationCount += mutations.length;
                window._lastMutationTime = Date.now();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: false
            });
            
            window._mutationObserver = observer;
        """)
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.driver.execute_script("""
                const now = Date.now();
                const timeSinceLastMutation = (now - window._lastMutationTime) / 1000;
                return {
                    mutations: window._mutationCount,
                    timeSince: timeSinceLastMutation,
                    stable: timeSinceLastMutation >= %f
                };
            """ % stable_time)
            
            if result['stable']:
                logger.debug(f"DOM stable after {time.time() - start_time:.2f}s ({result['mutations']} mutations)")
                # Cleanup
                self.driver.execute_script("window._mutationObserver.disconnect();")
                return True
            
            time.sleep(0.1)
        
        # Cleanup
        self.driver.execute_script("window._mutationObserver.disconnect();")
        logger.warning(f"DOM stability timeout after {max_wait}s")
        return False
    
    # =========================================================================
    # STRATEGY 3: Element Count Stabilization
    # =========================================================================
    
    def wait_for_element_count_stable(self, selector, stable_time=0.5, max_wait=10):
        """
        Wait for the count of matching elements to stop changing.
        
        Good for card lists, grids, etc.
        
        Args:
            selector: CSS selector or XPath for elements to count
            stable_time: Seconds without count change to consider "stable"
            max_wait: Maximum seconds to wait
            
        Returns:
            Final element count, or -1 if timeout
        """
        start_time = time.time()
        last_count = 0
        last_change_time = start_time
        
        while time.time() - start_time < max_wait:
            try:
                # Count elements
                if selector.startswith('//'):
                    # XPath
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    # CSS selector
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                current_count = len(elements)
                
                if current_count != last_count:
                    logger.debug(f"Element count changed: {last_count} → {current_count}")
                    last_count = current_count
                    last_change_time = time.time()
                elif time.time() - last_change_time >= stable_time:
                    logger.debug(f"Element count stable at {current_count} after {time.time() - start_time:.2f}s")
                    return current_count
                
                time.sleep(0.1)
            
            except Exception as e:
                logger.debug(f"Error counting elements: {e}")
                time.sleep(0.1)
        
        logger.warning(f"Element count stabilization timeout after {max_wait}s")
        return last_count if last_count > 0 else -1
    
    # =========================================================================
    # STRATEGY 4: Loading Indicator Detection
    # =========================================================================
    
    def wait_for_loading_indicator_gone(self, max_wait=10):
        """
        Wait for common loading indicators to disappear.
        
        Looks for spinners, "Loading..." text, skeleton loaders, etc.
        
        Args:
            max_wait: Maximum seconds to wait
            
        Returns:
            True if indicators disappeared, False if timeout
        """
        # Common loading indicator selectors
        loading_selectors = [
            ".loading",
            ".spinner",
            ".skeleton",
            "[class*='loading']",
            "[class*='spinner']",
            "[class*='skeleton']",
            "//*[contains(text(), 'Loading')]",
            "//*[contains(text(), 'loading')]",
        ]
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            indicators_present = False
            
            for selector in loading_selectors:
                try:
                    if selector.startswith('//'):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    # Check if any are visible
                    visible = [e for e in elements if e.is_displayed()]
                    if visible:
                        indicators_present = True
                        break
                
                except:
                    continue
            
            if not indicators_present:
                logger.debug(f"Loading indicators gone after {time.time() - start_time:.2f}s")
                return True
            
            time.sleep(0.1)
        
        logger.warning(f"Loading indicator timeout after {max_wait}s")
        return False
    
    # =========================================================================
    # STRATEGY 5: Combined Approach (Recommended)
    # =========================================================================
    
    def wait_for_dynamic_content(self, 
                                  card_selector="//a[contains(@href, '/cards/')]",
                                  strategy='combined',
                                  max_wait=10):
        """
        Wait for dynamic content using specified strategy or combination.
        
        Args:
            card_selector: Selector for card elements (for element count method)
            strategy: 'network', 'dom', 'elements', 'loading', 'combined'
            max_wait: Maximum seconds to wait
            
        Returns:
            True if content loaded, False if timeout
        """
        start_time = time.time()
        
        if strategy == 'network':
            return self.wait_for_network_idle(max_wait=max_wait)
        
        elif strategy == 'dom':
            return self.wait_for_dom_stable(max_wait=max_wait)
        
        elif strategy == 'elements':
            count = self.wait_for_element_count_stable(card_selector, max_wait=max_wait)
            return count > 0
        
        elif strategy == 'loading':
            return self.wait_for_loading_indicator_gone(max_wait=max_wait)
        
        elif strategy == 'combined':
            # Use multiple strategies in sequence
            logger.debug("Using combined strategy for dynamic content detection")
            
            # 1. First, wait for any loading indicators to disappear (fast check)
            self.wait_for_loading_indicator_gone(max_wait=2)
            
            # 2. Then wait for element count to stabilize (most reliable)
            count = self.wait_for_element_count_stable(card_selector, stable_time=0.3, max_wait=5)
            
            # 3. Finally, give a small buffer for any final DOM updates
            time.sleep(0.1)
            
            logger.debug(f"Combined strategy complete after {time.time() - start_time:.2f}s")
            return count > 0
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")


class EDHRecSmartScraper:
    """
    EDHREC scraper using advanced dynamic content detection.
    """
    
    BASE_URL = "https://edhrec.com"
    
    def __init__(self, output_dir: str = "data_sources_comprehensive/edhrec_smart", 
                 headless: bool = True,
                 strategy: str = 'combined'):
        """
        Initialize smart scraper.
        
        Args:
            output_dir: Output directory
            headless: Run headless
            strategy: Dynamic content detection strategy
                     ('network', 'dom', 'elements', 'loading', 'combined')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.headless = headless
        self.strategy = strategy
        self.driver = None
        self.content_handler = None
        
        self.commanders_data = []
    
    def _setup_driver(self):
        """Setup WebDriver with performance logging enabled."""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # Performance optimizations
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Enable performance logging for network monitoring
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Disable images for speed
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.content_handler = AdvancedDynamicContentHandler(self.driver)
            logger.info("✓ Smart WebDriver initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def _close_driver(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("✓ WebDriver closed")
    
    def _smart_scroll_and_wait(self, card_selector="//a[contains(@href, '/cards/')]"):
        """
        Perform intelligent scrolling with dynamic content detection.
        
        Args:
            card_selector: Selector for card elements
            
        Returns:
            Number of scrolls performed
        """
        scroll_count = 0
        max_scrolls = 50
        previous_card_count = 0
        no_new_cards_count = 0
        
        for scroll in range(max_scrolls):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_count += 1
            
            # Wait for content using selected strategy
            self.content_handler.wait_for_dynamic_content(
                card_selector=card_selector,
                strategy=self.strategy,
                max_wait=5
            )
            
            # Count current cards
            try:
                current_cards = len(self.driver.find_elements(By.XPATH, card_selector))
                
                if current_cards == previous_card_count:
                    no_new_cards_count += 1
                    if no_new_cards_count >= 3:
                        logger.debug(f"No new cards after 3 scrolls, stopping at {current_cards} cards")
                        break
                else:
                    logger.debug(f"Scroll {scroll_count}: {previous_card_count} → {current_cards} cards")
                    no_new_cards_count = 0
                    previous_card_count = current_cards
            
            except Exception as e:
                logger.debug(f"Error counting cards: {e}")
        
        logger.info(f"  Scrolled {scroll_count} times, found {previous_card_count} cards")
        return scroll_count
    
    def scrape_commander_page(self, commander_url: str, commander_name: str) -> Dict[str, Any]:
        """
        Scrape commander page using smart dynamic content detection.
        
        Args:
            commander_url: Commander page URL
            commander_name: Commander name
            
        Returns:
            Commander data with all cards
        """
        logger.info(f"Scraping: {commander_name}")
        
        try:
            self.driver.get(commander_url)
            
            # Wait for initial page load
            self.content_handler.wait_for_dynamic_content(strategy='loading', max_wait=5)
            
            # Perform smart scrolling
            scroll_count = self._smart_scroll_and_wait()
            
            # Extract cards (implementation same as before)
            cards = self._extract_all_cards()
            
            return {
                "commander": commander_name,
                "url": commander_url,
                "total_cards": len(cards),
                "all_cards": cards,
                "scroll_count": scroll_count,
                "strategy_used": self.strategy,
                "scraped_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scraping {commander_name}: {e}")
            return {
                "commander": commander_name,
                "url": commander_url,
                "error": str(e),
                "scraped_at": datetime.now().isoformat()
            }
    
    def _extract_all_cards(self) -> List[Dict[str, Any]]:
        """Extract all cards from current page."""
        cards = []
        seen = set()
        
        card_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/cards/')]")
        
        for elem in card_elements:
            try:
                name = elem.text.strip() or elem.get_attribute('title') or ''
                if name and name not in seen:
                    seen.add(name)
                    cards.append({
                        "name": name,
                        "url": elem.get_attribute('href'),
                        "scraped_at": datetime.now().isoformat()
                    })
            except:
                continue
        
        return cards


if __name__ == "__main__":
    import sys
    
    # Parse strategy from command line
    strategy = 'combined'  # default
    for arg in sys.argv[1:]:
        if arg.startswith('--strategy='):
            strategy = arg.split('=')[1]
    
    print(f"Using strategy: {strategy}")
    print("Available strategies:")
    print("  - network: Monitor network activity")
    print("  - dom: Watch DOM mutations")
    print("  - elements: Count element stabilization")
    print("  - loading: Wait for loading indicators")
    print("  - combined: Use multiple strategies (RECOMMENDED)")
    print()
    
    scraper = EDHRecSmartScraper(headless=True, strategy=strategy)
    
    # For now, just test setup
    if scraper._setup_driver():
        print("✓ Smart scraper initialized successfully")
        scraper._close_driver()
