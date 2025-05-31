#!/bin/bash

echo "GitHub Inbox Discord Bot Setup Script"
echo "====================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 18+ first."
    echo ""
    echo "Installation options:"
    echo "1. Using NodeSource repository (recommended):"
    echo "   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "   sudo apt-get install -y nodejs"
    echo ""
    echo "2. Using snap:"
    echo "   sudo snap install node --classic"
    echo ""
    echo "3. Using nvm (Node Version Manager):"
    echo "   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "   source ~/.bashrc"
    echo "   nvm install 18"
    echo "   nvm use 18"
    echo ""
    exit 1
fi

echo "✅ Node.js is installed: $(node --version)"
echo "✅ npm is installed: $(npm --version)"

# Install dependencies
echo ""
echo "Installing dependencies..."
npm install

# Build the project
echo ""
echo "Building the project..."
npm run build

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env: cp .env.example .env"
echo "2. Edit .env with your Discord and GitHub tokens"
echo "3. Run the bot: npm start"
echo ""
echo "For development with auto-reload: npm run dev"
