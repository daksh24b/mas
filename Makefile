.PHONY: help setup start stop restart logs test demo clean install

help:
	@echo "VeriFlow - Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup       - Run setup script (first time)"
	@echo "  make install     - Install Python dependencies"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make start       - Start all services (Docker Compose)"
	@echo "  make stop        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View service logs"
	@echo ""
	@echo "Development:"
	@echo "  make dev         - Start API in development mode"
	@echo "  make test        - Run system tests"
	@echo "  make demo        - Run demo script"
	@echo ""
	@echo "Data:"
	@echo "  make sample-data - Generate 50 sample claims"
	@echo "  make load-data   - Load WELFake dataset (set DATASET_PATH)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Remove cache and temp files"
	@echo "  make docs        - Open API documentation"
	@echo ""

setup:
	@echo "🚀 Running VeriFlow setup..."
	@./setup.sh

install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt

start:
	@echo "🐳 Starting VeriFlow services..."
	@docker-compose up -d
	@echo "✅ Services started!"
	@echo "   - API: http://localhost:8000"
	@echo "   - Docs: http://localhost:8000/docs"
	@echo "   - Qdrant: http://localhost:6333"

stop:
	@echo "🛑 Stopping VeriFlow services..."
	@docker-compose down

restart:
	@echo "🔄 Restarting VeriFlow services..."
	@docker-compose restart

logs:
	@docker-compose logs -f

dev:
	@echo "💻 Starting API in development mode..."
	@uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "🧪 Running system tests..."
	@python test_system.py

demo:
	@echo "🎬 Running demo..."
	@python demo.py

sample-data:
	@echo "📊 Generating sample data..."
	@python -m src.data_ingestion --type sample --count 50

load-data:
	@echo "📥 Loading dataset from $(DATASET_PATH)..."
	@python -m src.data_ingestion --type welfake --path $(DATASET_PATH) --limit 1000

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.log" -delete
	@echo "✅ Cleaned up cache and temp files"

docs:
	@echo "📚 Opening API documentation..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"

# Complete workflow
all: setup start sample-data test demo
	@echo ""
	@echo "🎉 VeriFlow is ready!"
	@echo "   Visit: http://localhost:8000/docs"
