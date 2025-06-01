#!/bin/bash

# GitHub Inbox Discord Bot Installation Script

set -e

echo "🤖 GitHub Inbox Discord Bot Installation"
echo "========================================"
echo

# Check if Python 3 is installed, install if missing
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python 3 is not installed. Installing Python 3..."
    
    # Detect OS and install Python accordingly
    if command -v apt &> /dev/null; then
        echo "📦 Detected Debian/Ubuntu system. Installing Python 3..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        echo "📦 Detected RHEL/CentOS system. Installing Python 3..."
        sudo yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        echo "📦 Detected Fedora system. Installing Python 3..."
        sudo dnf install -y python3 python3-pip
    elif command -v brew &> /dev/null; then
        echo "📦 Detected macOS system. Installing Python 3..."
        brew install python3
    else
        echo "❌ Unable to detect package manager. Please install Python 3.7+ manually:"
        echo "   Visit: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Verify installation
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 installation failed. Please install manually."
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION detected"

# Check if pip is installed, install if missing
if ! command -v pip3 &> /dev/null; then
    echo "⚠️  pip3 is not installed. Installing pip3..."
    
    # Try to install pip based on OS
    if command -v apt &> /dev/null; then
        sudo apt install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-pip
    else
        # Try using get-pip.py as fallback
        echo "📦 Installing pip using get-pip.py..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py --user
        rm get-pip.py
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Verify installation
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 installation failed. Please install manually."
        exit 1
    fi
fi

echo "✅ pip3 detected"

# Create virtual environment if it doesn't exist or is corrupted
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    if [ -d "venv" ]; then
        echo "⚠️  Virtual environment exists but is corrupted. Recreating..."
        rm -rf venv
    fi
    echo "📦 Creating virtual environment..."
    
    # Try to create virtual environment, install python3-venv if it fails
    if ! python3 -m venv venv 2>/dev/null; then
        echo "⚠️  Virtual environment creation failed. Installing python3-venv..."
        
        # Install python3-venv based on detected OS
        if command -v apt &> /dev/null; then
            PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            sudo apt update
            sudo apt install -y python3-venv python${PYTHON_VERSION}-venv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-venv
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-venv
        else
            echo "❌ Unable to install python3-venv automatically. Please install it manually."
            exit 1
        fi
        
        # Try creating virtual environment again
        echo "📦 Attempting to create virtual environment again..."
        if ! python3 -m venv venv; then
            echo "❌ Virtual environment creation failed even after installing python3-venv."
            exit 1
        fi
    fi
    
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
echo "   Dependencies to install:"
cat requirements.txt | sed 's/^/     - /'
echo
pip install -r requirements.txt
echo "✅ Dependencies installed successfully!"

# Check if configuration exists
if [ ! -f ".env" ]; then
    echo
    echo "⚙️  Configuration not found. Running setup..."
    python setup.py
    echo
else
    echo "✅ Configuration file (.env) already exists"
fi

# Test configuration
echo "🔍 Testing configuration..."
if python test_config.py; then
    echo
    echo "🎉 Installation completed successfully!"
    echo
    echo "Usage:"
    echo "  Start the bot:           ./start.sh"
    echo "  Stop the bot:            ./stop.sh"
    echo "  Check bot status:        ./status.sh"
    echo "  View bot logs:           ./logs.sh"
    echo "  Run configuration test:  python test_config.py"
    echo "  Reconfigure:             python setup.py"
    echo
    echo "To install as a systemd service:"
    echo "  sudo cp github-inbox-bot.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable github-inbox-bot"
    echo "  sudo systemctl start github-inbox-bot"
    echo
else
    echo
    echo "❌ Configuration test failed. Please run setup again:"
    echo "   python setup.py"
    exit 1
fi
