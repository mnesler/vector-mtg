# How to Fix Chromium for EDHREC Scraper

## The Problem

Your Chromium is installed via snap and has errors:
```
internal error, please report: running "chromium" failed: 
cannot find installed snap "chromium" at revision 3320
```

This prevents Selenium from using it for web scraping.

## The Solution

Run the fix script I created:

```bash
cd /home/maxwell/vector-mtg
bash fix_chromium.sh
```

This script will:
1. Remove the broken snap version
2. Install Chromium from apt (more stable)
3. Install chromedriver (required for Selenium)
4. Verify the installation

## Manual Steps (if you prefer)

If you want to run the commands manually:

```bash
# 1. Remove snap chromium
sudo snap remove chromium

# 2. Update package list
sudo apt-get update

# 3. Install chromium and chromedriver
sudo apt-get install -y chromium-browser chromium-chromedriver

# 4. Verify installation
chromium-browser --version
which chromedriver
```

## After Installation

Test the scraper:

```bash
cd /home/maxwell/vector-mtg
python scripts/test_chromium_scraper.py --strategy=elements
```

Expected output:
- Browser opens (headless)
- Scrolls through Atraxa commander page
- Shows progress: "Scroll 1... 25 cards (+25 new)"
- Extracts all cards (~250-300)
- Displays table with card names, synergy %, URLs

## Alternative: Download Chromedriver Manually

If apt installation doesn't work, download chromedriver directly:

```bash
# Check your chromium version first
chromium-browser --version

# Download matching chromedriver from:
# https://chromedriver.chromium.org/downloads

# Example for version 120:
cd /tmp
wget https://chromedriver.storage.googleapis.com/120.0.6099.109/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

## Troubleshooting

### Issue: "chromedriver not found"
```bash
# Find where chromedriver is installed
find /usr -name chromedriver 2>/dev/null

# Common locations:
/usr/bin/chromedriver
/usr/lib/chromium-browser/chromedriver
/snap/bin/chromium.chromedriver
```

### Issue: "chromium not found"
```bash
# Check if chromium is installed
which chromium-browser
dpkg -l | grep chromium
```

### Issue: Version mismatch
Chromium and chromedriver versions must be compatible. If you get version errors:

```bash
# Check versions
chromium-browser --version
chromedriver --version

# They should match major version numbers (e.g., both 120.x)
```

## Success Check

After fixing, you should be able to run:

```bash
python scripts/test_chromium_scraper.py --strategy=elements
```

And see output like:
```
Found chromedriver: /usr/bin/chromedriver
✓ Page loaded
Waiting for initial content...
✓ Initial content ready

Starting infinite scroll...
  Scroll 1... 25 cards (+25 new)
  Scroll 2... 50 cards (+25 new)
  ...
  Scroll 14... 268 cards (no change #3)

✓ No new cards after 3 scrolls, stopping
✓ Extracted 268 unique cards

[TABLE WITH ALL CARDS]
```

## Still Having Issues?

If Chromium installation is too problematic, we can:

1. **Use Firefox instead** (install geckodriver)
2. **Use a different approach** (headless Chrome in Docker)
3. **Use the demo** to verify the logic works:
   ```bash
   python scripts/demo_smart_scraper_output.py
   ```

Let me know if you need help with any of these alternatives!
