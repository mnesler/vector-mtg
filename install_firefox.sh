#!/bin/bash
# Switch to Firefox - Much More Reliable

echo "========================================="
echo "Installing Firefox for EDHREC Scraper"
echo "========================================="
echo ""

echo "Step 1: Installing Firefox and geckodriver..."
sudo apt-get update
sudo apt-get install -y firefox
echo "✓ Firefox installed"
echo ""

echo "Step 2: Installing geckodriver..."
# Check if geckodriver package exists
if apt-cache search geckodriver | grep -q geckodriver; then
    sudo apt-get install -y firefox-geckodriver
else
    echo "  Package 'firefox-geckodriver' not found, installing manually..."
    
    # Download geckodriver
    GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4)
    echo "  Latest geckodriver: $GECKODRIVER_VERSION"
    
    wget -q "https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz"
    tar -xzf "geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz"
    sudo mv geckodriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/geckodriver
    rm "geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz"
fi
echo "✓ Geckodriver installed"
echo ""

echo "Step 3: Verifying installation..."
echo "Firefox version:"
firefox --version

echo ""
echo "Geckodriver version:"
geckodriver --version | head -1
echo ""

echo "========================================="
echo "✓ Installation Complete!"
echo "========================================="
echo ""
echo "Firefox is now ready. The scraper will be updated to use Firefox."
echo ""
