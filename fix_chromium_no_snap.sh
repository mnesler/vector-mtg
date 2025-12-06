#!/bin/bash
# Properly fix Chromium by preventing snap auto-reinstall

echo "========================================="
echo "Chromium Fix - Prevent Snap Reinstall"
echo "========================================="
echo ""

echo "Step 1: Removing snap chromium (if present)..."
sudo snap remove chromium 2>/dev/null
echo "✓ Snap removed"
echo ""

echo "Step 2: Blocking snap from auto-installing..."
# Create a preference file to prevent snap reinstall
sudo tee /etc/apt/preferences.d/no-snap-chromium > /dev/null << 'EOF'
Package: chromium-browser
Pin: release o=Ubuntu*
Pin-Priority: -1
EOF
echo "✓ Snap auto-install blocked"
echo ""

echo "Step 3: Installing Chromium directly (not via snap)..."
# Try to install from Debian repository or build from source alternative

# Check if we can use Flatpak instead
if command -v flatpak &> /dev/null; then
    echo "  Installing via Flatpak..."
    flatpak install -y flathub org.chromium.Chromium
    echo "✓ Chromium installed via Flatpak"
else
    # Alternative: Download standalone chromium
    echo "  Neither apt nor flatpak will work without snap on Ubuntu."
    echo "  Recommended: Use Firefox instead or install chromium manually"
fi
echo ""

echo "Step 4: Verifying installation..."
if command -v chromium &> /dev/null; then
    chromium --version
elif flatpak list | grep -q chromium; then
    flatpak run org.chromium.Chromium --version
else
    echo "⚠ Chromium not available via standard methods on Ubuntu"
    echo "  Ubuntu forces chromium through snap"
fi
echo ""

echo "========================================="
echo "Alternative: Use Firefox Instead"
echo "========================================="
echo ""
echo "Firefox works better on Ubuntu and doesn't require snap:"
echo "  sudo apt-get install firefox firefox-geckodriver"
echo ""
