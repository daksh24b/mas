#!/bin/bash

# VeriFlow Setup Script
# This script sets up the VeriFlow environment

set -e

echo "🚀 VeriFlow Setup Script"
echo "========================"
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "   ❌ Error: Python 3.9+ is required"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip
echo "   ✅ Pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
echo "⚙️  Setting up configuration..."
if [ -f ".env" ]; then
    echo "   .env file already exists"
else
    cp .env.example .env
    echo "   ✅ Created .env file from template"
    echo "   ⚠️  Please edit .env file with your configuration"
fi
echo ""

# Check if Qdrant is running
echo "🔍 Checking Qdrant connection..."
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "   ✅ Qdrant is running"
else
    echo "   ⚠️  Qdrant is not running"
    echo "   Start Qdrant with: docker run -p 6333:6333 qdrant/qdrant"
fi
echo ""

# Download models (optional)
echo "🤖 Checking ML models..."
echo "   Models will be downloaded on first use"
echo "   This includes:"
echo "   - CLIP (openai/clip-vit-base-patch32): ~600MB"
echo "   - Whisper base model: ~140MB"
echo "   - Sentence Transformers: ~80MB"
echo ""
read -p "   Download models now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Downloading models..."
    python3 -c "
from transformers import CLIPModel, CLIPProcessor
import whisper
from sentence_transformers import SentenceTransformer
print('Loading CLIP...')
CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
print('Loading Whisper...')
whisper.load_model('base')
print('Loading Sentence Transformer...')
SentenceTransformer('all-MiniLM-L6-v2')
print('✅ All models downloaded')
"
fi
echo ""

# Generate sample data (optional)
read -p "📊 Generate sample data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Generating 50 sample claims..."
    python3 -m src.data_ingestion --type sample --count 50
    echo "   ✅ Sample data generated"
fi
echo ""

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env file with your configuration"
echo "   2. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant"
echo "   3. Start API: uvicorn src.main:app --reload"
echo "   4. Run demo: python demo.py"
echo "   5. Visit API docs: http://localhost:8000/docs"
echo ""
echo "🎉 Happy fact-checking!"
