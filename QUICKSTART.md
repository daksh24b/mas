# VeriFlow - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Check

```bash
# Check Python version (need 3.9+)
python3 --version

# Check Docker (for Qdrant)
docker --version
```

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone and enter directory
cd /path/to/mas

# 2. Start everything (API + Qdrant)
docker-compose up -d

# 3. Load sample data
docker-compose exec veriflow python -m src.data_ingestion --type sample --count 50

# 4. Visit API docs
open http://localhost:8000/docs

# 5. Run demo
docker-compose exec veriflow python demo.py
```

### Option 2: Manual Setup

```bash
# 1. Run setup script
chmod +x setup.sh
./setup.sh

# 2. Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# 3. Activate venv
source venv/bin/activate

# 4. Start API
uvicorn src.main:app --reload

# 5. In another terminal, run demo
python demo.py
```

## 📝 Your First Request

### Submit a Claim

```bash
curl -X POST "http://localhost:8000/claims/text" \
  -d "text=COVID-19 vaccines contain microchips" \
  -d "platform=twitter"
```

Response:
```json
{
  "claim_id": "abc123",
  "trust_score": 0.15,
  "trust_level": "debunked"
}
```

### Search for Claims

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "vaccine microchip", "limit": 5}'
```

### Get Provenance Report

```bash
curl "http://localhost:8000/claims/abc123/provenance"
```

## 🎨 Using the Interactive API Docs

1. Open http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

## 📊 Loading Your Own Data

### From WELFake Dataset

```bash
# Download WELFake from Kaggle
# https://www.kaggle.com/datasets/saurabhshahane/fake-news-classification

python -m src.data_ingestion \
  --type welfake \
  --path ~/Downloads/WELFake_Dataset.csv \
  --limit 1000
```

### From Custom JSON

Create `data.json`:
```json
[
  {
    "text": "Your claim here",
    "media_type": "text",
    "platform": "twitter",
    "is_verified": false,
    "tags": ["health", "covid"]
  }
]
```

Load it:
```bash
python -m src.data_ingestion \
  --type custom \
  --path data.json
```

## 🔍 Example Workflows

### Workflow 1: Verify a Suspicious Tweet

```python
import requests

# Submit claim
response = requests.post(
    "http://localhost:8000/claims/text",
    params={
        "text": "Drinking hot water prevents COVID-19",
        "platform": "twitter",
        "source_url": "https://twitter.com/example/123"
    }
)
claim_id = response.json()["claim_id"]

# Get provenance report
report = requests.get(
    f"http://localhost:8000/claims/{claim_id}/provenance"
).json()

print(f"Trust Level: {report['current_status']['trust_level']}")
print(f"Recommendation: {report['recommendation']}")
```

### Workflow 2: Upload Image for Verification

```python
import requests

# Upload image
with open("suspicious_image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/claims/image",
        files={"image": f},
        data={
            "platform": "instagram",
            "caption": "Optional caption"
        }
    )

claim_id = response.json()["claim_id"]

# Search for related claims (cross-modal)
search_response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "image content description",
        "media_type": "text",  # Find related TEXT claims
        "limit": 10
    }
)

print(f"Found {len(search_response.json()['results'])} related text claims")
```

### Workflow 3: Track Claim Evolution

```python
import requests
import time

# Submit original claim
claim_id = submit_claim("Initial claim text")

# Simulate evidence arriving over time
time.sleep(2)
add_evidence(claim_id, is_supporting=True, credibility=0.8)

time.sleep(2)
add_evidence(claim_id, is_supporting=False, credibility=0.9)

# Check evolution
provenance = requests.get(
    f"http://localhost:8000/claims/{claim_id}/provenance"
).json()

print("Trust Score History:")
for entry in provenance["timeline"]:
    print(f"  {entry['timestamp']}: {entry['description']}")
```

## 🛑 Troubleshooting

### Issue: "Connection refused" to Qdrant

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not, start it
docker run -d -p 6333:6333 qdrant/qdrant

# Test connection
curl http://localhost:6333/collections
```

### Issue: "Module not found"

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or use the setup script
./setup.sh
```

### Issue: Models downloading slowly

```bash
# Pre-download models
python3 -c "
from transformers import CLIPModel, CLIPProcessor
import whisper
CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
whisper.load_model('base')
"
```

### Issue: Out of memory

```bash
# Use smaller Whisper model
export WHISPER_MODEL=tiny

# Or reduce batch size in config
```

## 📚 Next Steps

1. **Read Full Documentation**: See [DOCUMENTATION.md](DOCUMENTATION.md)
2. **Explore API**: Visit http://localhost:8000/docs
3. **Run Demo**: `python demo.py`
4. **Load Real Data**: Use WELFake or custom datasets
5. **Customize**: Modify trust score algorithms in `src/trust_service.py`

## 🆘 Need Help?

- **API Documentation**: http://localhost:8000/docs
- **Technical Details**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **Architecture**: [README.md](README.md)
- **Code Examples**: [demo.py](demo.py)

## ✅ Verification Checklist

- [ ] Qdrant is running (port 6333)
- [ ] API is running (port 8000)
- [ ] Sample data is loaded
- [ ] Demo script runs successfully
- [ ] API docs are accessible
- [ ] Health check returns "healthy"

```bash
# Run all checks
curl http://localhost:6333/collections && \
curl http://localhost:8000/health && \
python demo.py && \
echo "✅ All systems operational!"
```

---

**Happy fact-checking! 🎉**
