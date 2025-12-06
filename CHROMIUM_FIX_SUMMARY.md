# Chromium Fix - Quick Summary

## What You Need to Do

Run this command:

```bash
cd /home/maxwell/vector-mtg
bash fix_chromium.sh
```

This will automatically fix the broken Chromium installation.

## What the Script Does

1. Removes broken snap Chromium
2. Installs Chromium from apt (stable version)
3. Installs chromedriver (Selenium needs this)
4. Verifies everything works

## After Running the Script

Test the scraper:

```bash
python scripts/test_chromium_scraper.py --strategy=elements
```

You should see:
- Scrolling progress
- Card extraction
- Table with ~250-300 cards from Atraxa page
- Synergy percentages
- Card URLs

## Files Created for You

1. **`fix_chromium.sh`** - Automated fix script (RUN THIS)
2. **`CHROMIUM_FIX_GUIDE.md`** - Detailed troubleshooting guide
3. **`test_chromium_scraper.py`** - Works with Chromium directly
4. **`test_static_scraper.py`** - Backup (no browser, limited data)

## Why Chromium is Broken

Your current Chromium is installed via snap and has a corrupted installation:
```
cannot find installed snap "chromium" at revision 3320
```

The apt version is more stable and compatible with Selenium.

## Quick Test Without Fixing

If you want to see the expected output first:

```bash
python scripts/demo_smart_scraper_output.py
```

This shows exactly what the real scraper will output (simulated data).

---

**Next step: Run `bash fix_chromium.sh` then test the scraper!**
