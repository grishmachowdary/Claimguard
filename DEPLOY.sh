#!/bin/bash
# ClaimGuard V2 Quick Deployment Script

set -e

echo "🚀 ClaimGuard V2 Production Deployment"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm not found. Please install Node.js 14+"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"
echo -e "${GREEN}✓ Node.js found${NC}"
echo ""

# Backend setup
echo -e "${BLUE}Setting up Backend...${NC}"
cd backend

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Download spaCy model
echo "Downloading spaCy model (this may take a minute)..."
python -m spacy download en_core_web_sm > /dev/null 2>&1

echo -e "${GREEN}✓ Backend dependencies installed${NC}"
cd ..
echo ""

# Frontend setup
echo -e "${BLUE}Setting up Frontend...${NC}"
cd frontend

echo "Installing Node dependencies..."
npm install > /dev/null 2>&1

echo "Building production bundle..."
npm run build > /dev/null 2>&1

echo -e "${GREEN}✓ Frontend built${NC}"
cd ..
echo ""

# Summary
echo -e "${GREEN}======================================"
echo "✅ ClaimGuard V2 Ready for Deployment"
echo "=====================================${NC}"
echo ""

echo "📋 Next Steps:"
echo ""
echo "1. Configure environment:"
echo "   cp backend/.env.example backend/.env"
echo "   # Edit backend/.env with production settings"
echo ""
echo "2. Start Backend:"
echo "   cd backend"
echo "   gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo ""
echo "3. Serve Frontend:"
echo "   cd frontend"
echo "   # Serve 'build/' directory with nginx, Apache, or:"
echo "   npm install -g serve && serve -s build -l 3000"
echo ""
echo "4. Test:"
echo "   # Open browser: http://localhost:3000"
echo "   # Login: customer@test.com / password123"
echo ""
echo "📖 Full guide: V2_PRODUCTION_DEPLOYMENT.md"
echo ""
