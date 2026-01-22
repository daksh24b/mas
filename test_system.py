"""
System test script to verify VeriFlow installation and functionality.
Run this after setup to ensure everything is working correctly.
"""

import sys
import importlib
from loguru import logger

def test_python_version():
    """Test Python version."""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False

def test_import(module_name, display_name=None):
    """Test if a module can be imported."""
    if display_name is None:
        display_name = module_name
    
    try:
        importlib.import_module(module_name)
        print(f"   ✅ {display_name}")
        return True
    except ImportError as e:
        print(f"   ❌ {display_name}: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are installed."""
    print("\n📦 Testing dependencies...")
    
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("qdrant_client", "Qdrant Client"),
        ("transformers", "Transformers"),
        ("torch", "PyTorch"),
        ("PIL", "Pillow"),
        ("whisper", "Whisper"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("sentence_transformers", "Sentence Transformers"),
    ]
    
    results = []
    for module, name in dependencies:
        results.append(test_import(module, name))
    
    return all(results)

def test_qdrant_connection():
    """Test connection to Qdrant."""
    print("\n🔌 Testing Qdrant connection...")
    
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print(f"   ✅ Connected to Qdrant")
        print(f"   📊 Found {len(collections.collections)} collections")
        return True
    except Exception as e:
        print(f"   ❌ Cannot connect to Qdrant: {e}")
        print(f"   💡 Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        return False

def test_models():
    """Test if ML models can be loaded."""
    print("\n🤖 Testing ML models...")
    
    try:
        print("   Loading CLIP...")
        from transformers import CLIPModel, CLIPProcessor
        model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
        processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
        print("   ✅ CLIP loaded successfully")
        
        print("   Loading Sentence Transformer...")
        from sentence_transformers import SentenceTransformer
        text_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("   ✅ Sentence Transformer loaded successfully")
        
        # Whisper is slower, skip for quick test
        print("   ⏭️  Skipping Whisper (will load on first audio upload)")
        
        return True
    except Exception as e:
        print(f"   ❌ Failed to load models: {e}")
        return False

def test_api_imports():
    """Test if the VeriFlow modules can be imported."""
    print("\n🔧 Testing VeriFlow modules...")
    
    modules = [
        "src.config",
        "src.models",
        "src.qdrant_service",
        "src.embedding_service",
        "src.trust_service",
        "src.search_service",
        "src.main",
    ]
    
    results = []
    for module in modules:
        results.append(test_import(module))
    
    return all(results)

def test_embedding_generation():
    """Test embedding generation."""
    print("\n🧠 Testing embedding generation...")
    
    try:
        from src.embedding_service import embedding_service
        
        # Test text embedding
        print("   Testing text embedding...")
        text_embedding = embedding_service.embed_text("This is a test")
        assert len(text_embedding) == 512, f"Expected 512D, got {len(text_embedding)}D"
        print(f"   ✅ Text embedding: {len(text_embedding)}D")
        
        # Test image embedding
        print("   Testing image embedding...")
        from PIL import Image
        import numpy as np
        test_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        image_embedding = embedding_service.embed_image(test_image)
        assert len(image_embedding) == 512, f"Expected 512D, got {len(image_embedding)}D"
        print(f"   ✅ Image embedding: {len(image_embedding)}D")
        
        return True
    except Exception as e:
        print(f"   ❌ Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qdrant_operations():
    """Test Qdrant operations."""
    print("\n💾 Testing Qdrant operations...")
    
    try:
        from src.qdrant_service import qdrant_service
        from src.models import ClaimMetadata, MediaType, Platform, TrustLevel
        from datetime import datetime
        import uuid
        
        # Create collection
        print("   Creating/verifying collection...")
        qdrant_service.create_collection()
        print("   ✅ Collection ready")
        
        # Insert test claim
        print("   Inserting test claim...")
        test_embedding = [0.1] * 512
        test_metadata = ClaimMetadata(
            claim_id=f"test_{uuid.uuid4()}",
            media_type=MediaType.TEXT,
            platform=Platform.TWITTER,
            timestamp=datetime.utcnow(),
            trust_score=0.5,
            trust_level=TrustLevel.UNCERTAIN,
            last_updated=datetime.utcnow(),
            original_text="Test claim",
            tags=["test"],
        )
        
        point_id = qdrant_service.insert_claim(test_embedding, test_metadata)
        print(f"   ✅ Inserted claim: {point_id}")
        
        # Search
        print("   Searching claims...")
        results = qdrant_service.search_claims(test_embedding, limit=5)
        print(f"   ✅ Found {len(results)} results")
        
        return True
    except Exception as e:
        print(f"   ❌ Qdrant operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trust_calculator():
    """Test trust score calculation."""
    print("\n📊 Testing trust score calculator...")
    
    try:
        from src.trust_service import trust_calculator
        
        # Test initial score
        score = trust_calculator.calculate_initial_score(0.8, 0.6)
        assert 0.0 <= score <= 1.0, f"Score {score} out of range"
        print(f"   ✅ Initial score calculation: {score:.2f}")
        
        # Test trust level determination
        level = trust_calculator.determine_trust_level(0.85)
        print(f"   ✅ Trust level determination: {level.value}")
        
        return True
    except Exception as e:
        print(f"   ❌ Trust calculator failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary."""
    print("=" * 80)
    print("  VeriFlow System Test")
    print("=" * 80)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("VeriFlow Modules", test_api_imports),
        ("Qdrant Connection", test_qdrant_connection),
        ("ML Models", test_models),
        ("Embedding Generation", test_embedding_generation),
        ("Qdrant Operations", test_qdrant_operations),
        ("Trust Calculator", test_trust_calculator),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("  Test Summary")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print("\n" + "-" * 80)
    print(f"  {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! VeriFlow is ready to use.")
        print("\nNext steps:")
        print("  1. Start API: uvicorn src.main:app --reload")
        print("  2. Run demo: python demo.py")
        print("  3. Visit: http://localhost:8000/docs")
        return True
    else:
        print("\n⚠️  Some tests failed. Please fix issues before proceeding.")
        print("\nTroubleshooting:")
        if not results.get("Dependencies"):
            print("  - Install dependencies: pip install -r requirements.txt")
        if not results.get("Qdrant Connection"):
            print("  - Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        if not results.get("ML Models"):
            print("  - Models will download on first use (requires internet)")
        return False
    
    print("=" * 80)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
