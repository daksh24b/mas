"""
Data ingestion utilities for loading datasets into VeriFlow.

Supports:
- WELFake dataset (text-based fake news)
- Custom CSV/JSON datasets
- Fact-check API integration
"""

import pandas as pd
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from loguru import logger
from pathlib import Path

from src.qdrant_service import qdrant_service
from src.embedding_service import embedding_service
from src.models import ClaimMetadata, MediaType, Platform, TrustLevel
from src.trust_service import trust_calculator


class DataIngestionService:
    """Service for ingesting various datasets into VeriFlow."""
    
    def __init__(self):
        """Initialize data ingestion service."""
        self.qdrant = qdrant_service
        self.embedder = embedding_service
    
    def ingest_welfake_dataset(
        self,
        csv_path: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ingest WELFake dataset.
        
        Expected columns: title, text, label (0=fake, 1=real)
        """
        try:
            logger.info(f"Loading WELFake dataset from {csv_path}")
            df = pd.read_csv(csv_path)
            
            if limit:
                df = df.head(limit)
            
            ingested_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # Extract data
                    title = str(row.get("title", ""))
                    text = str(row.get("text", ""))
                    label = int(row.get("label", 0))
                    
                    # Combine title and text
                    full_text = f"{title}\n\n{text}" if title else text
                    
                    # Generate embedding
                    embedding = self.embedder.embed_text(full_text)
                    
                    # Calculate trust score based on label
                    if label == 1:  # Real news
                        trust_score = random.uniform(0.7, 0.95)
                    else:  # Fake news
                        trust_score = random.uniform(0.1, 0.4)
                    
                    # Create metadata
                    metadata = ClaimMetadata(
                        claim_id=f"welfake_{idx}",
                        media_type=MediaType.TEXT,
                        platform=Platform.NEWS_WEBSITE,
                        source_url=f"https://example.com/article/{idx}",
                        timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                        trust_score=trust_score,
                        trust_level=trust_calculator.determine_trust_level(trust_score),
                        last_updated=datetime.utcnow(),
                        original_text=full_text[:500],  # Store first 500 chars
                        tags=["welfake", "news", "real" if label == 1 else "fake"],
                    )
                    
                    # Insert into Qdrant
                    self.qdrant.insert_claim(embedding, metadata)
                    ingested_count += 1
                    
                    if ingested_count % 100 == 0:
                        logger.info(f"Ingested {ingested_count} claims...")
                    
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
                    logger.warning(f"Failed to ingest row {idx}: {e}")
            
            logger.info(f"Successfully ingested {ingested_count} claims from WELFake")
            
            return {
                "dataset": "WELFake",
                "total_processed": len(df),
                "successfully_ingested": ingested_count,
                "errors": len(errors),
                "error_details": errors[:10],  # First 10 errors
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest WELFake dataset: {e}")
            raise
    
    def ingest_custom_json(
        self,
        json_path: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ingest custom JSON dataset.
        
        Expected format:
        [
            {
                "text": "claim text",
                "media_type": "text/image/audio",
                "platform": "twitter/facebook/etc",
                "source_url": "url",
                "is_verified": true/false,
                "tags": ["tag1", "tag2"]
            },
            ...
        ]
        """
        try:
            logger.info(f"Loading custom dataset from {json_path}")
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            if limit:
                data = data[:limit]
            
            ingested_count = 0
            errors = []
            
            for idx, item in enumerate(data):
                try:
                    # Extract data
                    text = item.get("text", "")
                    media_type = MediaType(item.get("media_type", "text"))
                    platform = Platform(item.get("platform", "other"))
                    source_url = item.get("source_url")
                    is_verified = item.get("is_verified", False)
                    tags = item.get("tags", [])
                    
                    # Generate embedding
                    embedding = self.embedder.embed_text(text)
                    
                    # Calculate trust score
                    trust_score = random.uniform(0.7, 0.95) if is_verified else random.uniform(0.3, 0.6)
                    
                    # Create metadata
                    metadata = ClaimMetadata(
                        claim_id=f"custom_{idx}",
                        media_type=media_type,
                        platform=platform,
                        source_url=source_url,
                        timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 180)),
                        trust_score=trust_score,
                        trust_level=trust_calculator.determine_trust_level(trust_score),
                        last_updated=datetime.utcnow(),
                        original_text=text,
                        tags=tags,
                    )
                    
                    # Insert into Qdrant
                    self.qdrant.insert_claim(embedding, metadata)
                    ingested_count += 1
                    
                except Exception as e:
                    errors.append(f"Item {idx}: {str(e)}")
                    logger.warning(f"Failed to ingest item {idx}: {e}")
            
            logger.info(f"Successfully ingested {ingested_count} claims from custom JSON")
            
            return {
                "dataset": "Custom JSON",
                "total_processed": len(data),
                "successfully_ingested": ingested_count,
                "errors": len(errors),
                "error_details": errors[:10],
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest custom JSON: {e}")
            raise
    
    def generate_sample_data(self, count: int = 50) -> Dict[str, Any]:
        """Generate sample synthetic data for testing."""
        try:
            logger.info(f"Generating {count} sample claims...")
            
            sample_claims = [
                "COVID-19 vaccines contain microchips for tracking",
                "Climate change is a natural cycle, not human-caused",
                "5G networks cause coronavirus infections",
                "Election results were manipulated by foreign hackers",
                "Drinking bleach can cure COVID-19",
                "Scientists discover cure for all cancers",
                "Earth is flat, NASA photos are fake",
                "Moon landing was staged in a Hollywood studio",
                "Aliens built the Egyptian pyramids",
                "Drinking hot water prevents coronavirus",
            ]
            
            platforms = list(Platform)
            
            ingested_count = 0
            
            for i in range(count):
                try:
                    # Select random claim
                    claim_text = random.choice(sample_claims)
                    claim_text = f"{claim_text} (variant {i})"
                    
                    # Generate embedding
                    embedding = self.embedder.embed_text(claim_text)
                    
                    # Random trust score
                    trust_score = random.uniform(0.1, 0.9)
                    
                    # Create metadata
                    metadata = ClaimMetadata(
                        claim_id=f"sample_{i}",
                        media_type=random.choice(list(MediaType)),
                        platform=random.choice(platforms),
                        source_url=f"https://example.com/claim/{i}",
                        timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                        trust_score=trust_score,
                        trust_level=trust_calculator.determine_trust_level(trust_score),
                        verification_count=random.randint(0, 10),
                        supporting_evidence_count=random.randint(0, 5),
                        refuting_evidence_count=random.randint(0, 5),
                        last_updated=datetime.utcnow(),
                        original_text=claim_text,
                        tags=["sample", "synthetic"],
                    )
                    
                    # Insert into Qdrant
                    self.qdrant.insert_claim(embedding, metadata)
                    ingested_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to generate sample {i}: {e}")
            
            logger.info(f"Successfully generated {ingested_count} sample claims")
            
            return {
                "dataset": "Sample Synthetic Data",
                "total_generated": count,
                "successfully_ingested": ingested_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate sample data: {e}")
            raise


# Global instance
data_ingestion = DataIngestionService()


# CLI interface for data ingestion
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest data into VeriFlow")
    parser.add_argument(
        "--type",
        choices=["welfake", "custom", "sample"],
        required=True,
        help="Type of data to ingest"
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to dataset file (for welfake or custom)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of records to ingest"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of sample records to generate (for sample type)"
    )
    
    args = parser.parse_args()
    
    # Initialize Qdrant collection
    qdrant_service.create_collection()
    
    # Perform ingestion
    if args.type == "welfake":
        if not args.path:
            parser.error("--path is required for welfake type")
        result = data_ingestion.ingest_welfake_dataset(args.path, args.limit)
    elif args.type == "custom":
        if not args.path:
            parser.error("--path is required for custom type")
        result = data_ingestion.ingest_custom_json(args.path, args.limit)
    elif args.type == "sample":
        result = data_ingestion.generate_sample_data(args.count)
    
    print("\nIngestion Result:")
    print(json.dumps(result, indent=2))
