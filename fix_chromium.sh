#!/bin/bash
# Fix Chromium Installation for Scraping
# Run this script to fix the broken Chromium snap installation

echo "========================================="
echo "Chromium Fix Script for EDHREC Scraper"
echo "========================================="
echo ""

echo "Step 1: Removing broken snap Chromium..."
sudo snap remove chromium
echo "✓ Snap chromium removed"
echo ""

echo "Step 2: Installing Chromium from apt..."
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
echo "✓ Chromium and chromedriver installed"
echo ""

echo "Step 3: Verifying installation..."
echo "Chromium version:"
chromium-browser --version 2>&1 | grep -v "xdg-settings" || echo "  (installed but may show warnings)"

echo ""
echo "Chromedriver location:"
which chromedriver || echo "  Not in PATH, checking other locations..."
ls -la /usr/bin/chromedriver /usr/lib/chromium-browser/chromedriver 2>/dev/null | head -2
echo ""

echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Now test the scraper with:"
echo "  python scripts/test_chromium_scraper.py --strategy=elements"
echo ""
