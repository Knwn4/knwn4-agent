#!/bin/bash
# deploy/setup.sh — Run on VPS (jah-prod-01) as root
set -euo pipefail

echo "=== KNWN4 Content Agent — VPS Setup ==="

# Install system deps
apt-get update && apt-get install -y python3.11 python3.11-venv ffmpeg git curl

# Install Doppler CLI
if ! command -v doppler &> /dev/null; then
    echo "Installing Doppler..."
    curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://get.doppler.com' | sh
fi

# Install Node.js (for Playwright + Remotion)
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# Install Playwright browsers
npx playwright install --with-deps chromium

# Clone or update project
if [ -d /opt/knwn4-agent ]; then
    echo "Updating existing installation..."
    cd /opt/knwn4-agent
    git pull
else
    echo "Cloning project..."
    git clone git@github.com:elitanenbaum/knwn4-agent.git /opt/knwn4-agent
    cd /opt/knwn4-agent
fi

# Setup Python venv
if [ ! -d .venv ]; then
    python3.11 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .

# Clone content project (for reference files: BRAND.md, voice-master.md, etc.)
if [ ! -d /opt/knwn4-content ]; then
    git clone git@github.com:elitanenbaum/CONTENTCREATORJAH.git /opt/knwn4-content
fi

# Create required directories
mkdir -p /opt/knwn4-agent/browser-profiles
mkdir -p /opt/knwn4-agent/media/{voiceovers,assembled,exports,remotion}

# Set ownership
chown -R jah:jah /opt/knwn4-agent /opt/knwn4-content

# Install and enable systemd service
cp deploy/knwn4-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable knwn4-agent
systemctl restart knwn4-agent

echo ""
echo "=== Setup complete ==="
echo "Service status:"
systemctl status knwn4-agent --no-pager
echo ""
echo "Logs: journalctl -u knwn4-agent -f"
echo "Doppler: doppler run --project knwn4-agent --config prd -- env | grep -c ."
