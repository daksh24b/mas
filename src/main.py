from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, List
import uuid
from loguru import logger
import tempfile
import os

from src.models import (
    ClaimInput,
    SearchQuery,
    ProvenanceReport,
    HealthCheck,
    ClaimMetadata,
    EvidenceEntry,
    MediaType,
    Platform,
    TrustLevel,
)
from src.qdrant_service import qdrant_service
from src.embedding_service import embedding_service
from src.trust_service import trust_calculator, memory_manager
from src.config import settings


# Initialize FastAPI app
app = FastAPI(
    title="VeriFlow API",
    description="Multimodal Digital Trust & Forensic Memory Agent",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting VeriFlow API...")
    
    # Initialize Qdrant collection
    try:
        qdrant_service.create_collection(embedding_dim=512)
        logger.info("Qdrant collection ready")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        raise
    
    logger.info("VeriFlow API started successfully")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "VeriFlow: Multimodal Digital Trust & Forensic Memory Agent",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Check the health status of the service."""
    qdrant_healthy = qdrant_service.health_check()
    
    return HealthCheck(
        status="healthy" if qdrant_healthy else "degraded",
        qdrant_connected=qdrant_healthy,
    )


@app.post("/claims/text", tags=["Claims"])
async def submit_text_claim(
    text: str,
    platform: Platform,
    source_url: Optional[str] = None,
    tags: List[str] = Query(default=[]),
):
    """Submit a text-based claim for verification."""
    try:
        # Generate embedding
        embedding = embedding_service.embed_text(text)
        
        # Create metadata
        claim_id = str(uuid.uuid4())
        metadata = ClaimMetadata(
            claim_id=claim_id,
            media_type=MediaType.TEXT,
            platform=platform,
            source_url=source_url,
            timestamp=datetime.utcnow(),
            trust_score=trust_calculator.calculate_initial_score(),
            trust_level=TrustLevel.UNCERTAIN,
            last_updated=datetime.utcnow(),
            original_text=text,
            tags=tags,
        )
        
        # Insert into Qdrant
        point_id = qdrant_service.insert_claim(embedding, metadata)
        
        return {
            "claim_id": point_id,
            "status": "success",
            "message": "Text claim submitted successfully",
            "trust_score": metadata.trust_score,
            "trust_level": metadata.trust_level.value,
        }
        
    except Exception as e:
        logger.error(f"Error submitting text claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/claims/image", tags=["Claims"])
async def submit_image_claim(
    image: UploadFile = File(...),
    platform: Platform = Platform.OTHER,
    source_url: Optional[str] = None,
    caption: Optional[str] = None,
    tags: List[str] = Query(default=[]),
):
    """Submit an image-based claim for verification."""
    try:
        # Read image
        image_bytes = await image.read()
        
        # Generate embedding
        if caption:
            # Multimodal embedding with both image and caption
            embedding, _ = embedding_service.embed_multimodal(
                text=caption,
                image=image_bytes
            )
        else:
            # Image-only embedding
            embedding = embedding_service.embed_image(image_bytes)
        
        # Create metadata
        claim_id = str(uuid.uuid4())
        metadata = ClaimMetadata(
            claim_id=claim_id,
            media_type=MediaType.IMAGE,
            platform=platform,
            source_url=source_url,
            timestamp=datetime.utcnow(),
            trust_score=trust_calculator.calculate_initial_score(),
            trust_level=TrustLevel.UNCERTAIN,
            last_updated=datetime.utcnow(),
            original_text=caption,
            tags=tags,
        )
        
        # Insert into Qdrant
        point_id = qdrant_service.insert_claim(embedding, metadata)
        
        return {
            "claim_id": point_id,
            "status": "success",
            "message": "Image claim submitted successfully",
            "trust_score": metadata.trust_score,
            "trust_level": metadata.trust_level.value,
        }
        
    except Exception as e:
        logger.error(f"Error submitting image claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/claims/audio", tags=["Claims"])
async def submit_audio_claim(
    audio: UploadFile = File(...),
    platform: Platform = Platform.PODCAST,
    source_url: Optional[str] = None,
    tags: List[str] = Query(default=[]),
):
    """Submit an audio-based claim for verification."""
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_bytes = await audio.read()
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        try:
            # Generate embedding and transcription
            embedding, transcription = embedding_service.embed_audio(temp_audio_path)
            
            # Create metadata
            claim_id = str(uuid.uuid4())
            metadata = ClaimMetadata(
                claim_id=claim_id,
                media_type=MediaType.AUDIO,
                platform=platform,
                source_url=source_url,
                timestamp=datetime.utcnow(),
                trust_score=trust_calculator.calculate_initial_score(),
                trust_level=TrustLevel.UNCERTAIN,
                last_updated=datetime.utcnow(),
                transcription=transcription,
                tags=tags,
            )
            
            # Insert into Qdrant
            point_id = qdrant_service.insert_claim(embedding, metadata)
            
            return {
                "claim_id": point_id,
                "status": "success",
                "message": "Audio claim submitted successfully",
                "transcription": transcription,
                "trust_score": metadata.trust_score,
                "trust_level": metadata.trust_level.value,
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_audio_path)
        
    except Exception as e:
        logger.error(f"Error submitting audio claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", tags=["Search"])
async def search_claims(query: SearchQuery):
    """Search for claims using text query and filters."""
    try:
        # Generate query embedding
        if query.query:
            query_embedding = embedding_service.embed_text(query.query)
        else:
            raise HTTPException(status_code=400, detail="Query text is required")
        
        # Build filters
        filters = {}
        if query.media_type:
            filters["media_type"] = query.media_type.value
        if query.platform:
            filters["platform"] = query.platform.value
        if query.trust_level:
            filters["trust_level"] = query.trust_level.value
        if query.min_trust_score is not None:
            filters["min_trust_score"] = query.min_trust_score
        if query.max_trust_score is not None:
            filters["max_trust_score"] = query.max_trust_score
        
        # Search Qdrant
        results = qdrant_service.search_claims(
            query_vector=query_embedding,
            limit=query.limit,
            filters=filters,
        )
        
        return {
            "query": query.query,
            "total_results": len(results),
            "results": results,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching claims: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims/{claim_id}", tags=["Claims"])
async def get_claim(claim_id: str):
    """Retrieve a specific claim by ID."""
    try:
        claim = qdrant_service.get_claim_by_id(claim_id)
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        return claim
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims/{claim_id}/provenance", response_model=ProvenanceReport, tags=["Claims"])
async def get_provenance_report(claim_id: str):
    """Generate a comprehensive provenance report for a claim."""
    try:
        # Get the claim
        claim_data = qdrant_service.get_claim_by_id(claim_id)
        
        if not claim_data:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Parse metadata
        payload = claim_data["payload"]
        claim_metadata = ClaimMetadata(
            claim_id=payload["claim_id"],
            media_type=MediaType(payload["media_type"]),
            platform=Platform(payload["platform"]),
            source_url=payload.get("source_url"),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            trust_score=payload["trust_score"],
            trust_level=TrustLevel(payload["trust_level"]),
            verification_count=payload.get("verification_count", 0),
            supporting_evidence_count=payload.get("supporting_evidence_count", 0),
            refuting_evidence_count=payload.get("refuting_evidence_count", 0),
            last_updated=datetime.fromisoformat(payload["last_updated"]),
            original_text=payload.get("original_text"),
            transcription=payload.get("transcription"),
            tags=payload.get("tags", []),
        )
        
        # Get related claims
        related_results = qdrant_service.get_related_claims(claim_id, limit=5)
        related_claims = [
            ClaimMetadata(
                claim_id=r["payload"]["claim_id"],
                media_type=MediaType(r["payload"]["media_type"]),
                platform=Platform(r["payload"]["platform"]),
                source_url=r["payload"].get("source_url"),
                timestamp=datetime.fromisoformat(r["payload"]["timestamp"]),
                trust_score=r["payload"]["trust_score"],
                trust_level=TrustLevel(r["payload"]["trust_level"]),
                last_updated=datetime.fromisoformat(r["payload"]["last_updated"]),
                original_text=r["payload"].get("original_text"),
                tags=r["payload"].get("tags", []),
            )
            for r in related_results
        ]
        
        # For this demo, create mock evidence (in production, this would come from a database)
        evidence_trail = []
        
        # Generate timeline
        timeline = memory_manager.generate_timeline(
            claim_metadata,
            evidence_trail,
            related_claims,
        )
        
        # Generate evidence summary
        evidence_summary = memory_manager.generate_evidence_summary(evidence_trail)
        
        # Generate trust assessment
        trust_level = claim_metadata.trust_level
        trust_assessment = f"Current trust level: {trust_level.value.replace('_', ' ').title()} "
        trust_assessment += f"(score: {claim_metadata.trust_score:.2f}). "
        
        if trust_level == TrustLevel.VERIFIED:
            trust_assessment += "This claim has been verified by multiple credible sources."
        elif trust_level == TrustLevel.LIKELY_TRUE:
            trust_assessment += "This claim is likely true based on available evidence."
        elif trust_level == TrustLevel.UNCERTAIN:
            trust_assessment += "Insufficient evidence to determine the veracity of this claim."
        elif trust_level == TrustLevel.LIKELY_FALSE:
            trust_assessment += "This claim is likely false based on available evidence."
        else:  # DEBUNKED
            trust_assessment += "This claim has been debunked by authoritative sources."
        
        # Generate recommendation
        if trust_level in [TrustLevel.VERIFIED, TrustLevel.LIKELY_TRUE]:
            recommendation = "This claim appears credible. However, always verify with primary sources."
        elif trust_level == TrustLevel.UNCERTAIN:
            recommendation = "Exercise caution. More evidence is needed to assess this claim's veracity."
        else:
            recommendation = "This claim is unreliable. Do not share without fact-checking."
        
        # Build report
        report = ProvenanceReport(
            claim_id=claim_id,
            current_status=claim_metadata,
            trust_assessment=trust_assessment,
            evidence_summary=evidence_summary,
            timeline=timeline,
            related_claims=related_claims,
            recommendation=recommendation,
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating provenance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/claims/{claim_id}/trust-score", tags=["Claims"])
async def update_trust_score(
    claim_id: str,
    new_score: float = Query(..., ge=0.0, le=1.0),
    reason: Optional[str] = None,
):
    """Update the trust score for a claim."""
    try:
        # Determine new trust level
        new_level = trust_calculator.determine_trust_level(new_score)
        
        # Update in Qdrant
        qdrant_service.update_trust_score(
            claim_id=claim_id,
            new_trust_score=new_score,
            new_trust_level=new_level,
        )
        
        return {
            "claim_id": claim_id,
            "new_trust_score": new_score,
            "new_trust_level": new_level.value,
            "reason": reason,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error updating trust score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
