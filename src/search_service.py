from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from src.qdrant_service import qdrant_service
from src.embedding_service import embedding_service
from src.models import ClaimMetadata, MediaType, Platform, TrustLevel


class HybridSearchService:
    """
    Advanced hybrid search combining semantic similarity with metadata filtering
    and traceable reasoning chains.
    """
    
    def __init__(self):
        """Initialize hybrid search service."""
        self.qdrant = qdrant_service
        self.embedder = embedding_service
    
    def search_with_reasoning(
        self,
        query: str,
        media_type: Optional[MediaType] = None,
        platform: Optional[Platform] = None,
        trust_threshold: float = 0.0,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search with explainable reasoning chains.
        
        Returns results with reasoning paths explaining why each result was matched.
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)
            
            # Build filters
            filters = {}
            if media_type:
                filters["media_type"] = media_type.value
            if platform:
                filters["platform"] = platform.value
            if trust_threshold > 0:
                filters["min_trust_score"] = trust_threshold
            
            # Perform search
            results = self.qdrant.search_claims(
                query_vector=query_embedding,
                limit=limit * 2,  # Get more for re-ranking
                filters=filters,
            )
            
            # Add reasoning chains
            reasoned_results = []
            for result in results:
                reasoning = self._build_reasoning_chain(
                    query=query,
                    result=result,
                    filters=filters,
                )
                
                result["reasoning"] = reasoning
                result["reasoning_score"] = self._calculate_reasoning_score(reasoning)
                reasoned_results.append(result)
            
            # Re-rank by reasoning score
            reasoned_results.sort(
                key=lambda x: (x["reasoning_score"], x["score"]),
                reverse=True
            )
            
            # Return top results
            return {
                "query": query,
                "total_found": len(reasoned_results),
                "results": reasoned_results[:limit],
                "search_metadata": {
                    "filters_applied": filters,
                    "semantic_search": True,
                    "reasoning_enabled": True,
                }
            }
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise
    
    def _build_reasoning_chain(
        self,
        query: str,
        result: Dict[str, Any],
        filters: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Build a reasoning chain explaining why this result matches."""
        chain = []
        
        # Semantic similarity reasoning
        similarity_score = result["score"]
        if similarity_score > 0.8:
            chain.append({
                "step": "semantic_match",
                "reason": f"Very high semantic similarity ({similarity_score:.3f}) to query",
                "confidence": "high"
            })
        elif similarity_score > 0.6:
            chain.append({
                "step": "semantic_match",
                "reason": f"Good semantic similarity ({similarity_score:.3f}) to query",
                "confidence": "medium"
            })
        else:
            chain.append({
                "step": "semantic_match",
                "reason": f"Moderate semantic similarity ({similarity_score:.3f}) to query",
                "confidence": "low"
            })
        
        # Metadata reasoning
        payload = result["payload"]
        
        # Media type match
        if "media_type" in filters:
            chain.append({
                "step": "media_type_filter",
                "reason": f"Matches required media type: {payload['media_type']}",
                "confidence": "high"
            })
        
        # Platform match
        if "platform" in filters:
            chain.append({
                "step": "platform_filter",
                "reason": f"Matches required platform: {payload['platform']}",
                "confidence": "high"
            })
        
        # Trust score reasoning
        trust_score = payload.get("trust_score", 0.5)
        trust_level = payload.get("trust_level", "uncertain")
        
        if trust_score >= 0.7:
            chain.append({
                "step": "trust_assessment",
                "reason": f"High trust score ({trust_score:.2f}) indicates reliability",
                "confidence": "high"
            })
        elif trust_score <= 0.3:
            chain.append({
                "step": "trust_assessment",
                "reason": f"Low trust score ({trust_score:.2f}) indicates unreliability",
                "confidence": "high"
            })
        
        # Verification reasoning
        verification_count = payload.get("verification_count", 0)
        if verification_count > 0:
            chain.append({
                "step": "verification",
                "reason": f"Claim has been verified {verification_count} time(s)",
                "confidence": "medium"
            })
        
        # Temporal reasoning
        timestamp = datetime.fromisoformat(payload["timestamp"])
        age_days = (datetime.utcnow() - timestamp).days
        
        if age_days < 7:
            chain.append({
                "step": "temporal",
                "reason": f"Recent claim ({age_days} days old)",
                "confidence": "medium"
            })
        elif age_days > 180:
            chain.append({
                "step": "temporal",
                "reason": f"Older claim ({age_days} days old) - may need re-verification",
                "confidence": "low"
            })
        
        return chain
    
    def _calculate_reasoning_score(self, reasoning_chain: List[Dict[str, str]]) -> float:
        """Calculate an overall reasoning score from the chain."""
        confidence_weights = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.3,
        }
        
        if not reasoning_chain:
            return 0.0
        
        total_confidence = sum(
            confidence_weights.get(step["confidence"], 0.5)
            for step in reasoning_chain
        )
        
        # Normalize by chain length
        return total_confidence / len(reasoning_chain)
    
    def find_claim_evolution_path(
        self,
        claim_id: str,
        max_hops: int = 3,
    ) -> Dict[str, Any]:
        """
        Trace the evolution path of a claim through related claims.
        
        This creates a graph showing how information has morphed across platforms.
        """
        try:
            # Get the original claim
            original = self.qdrant.get_claim_by_id(claim_id)
            if not original:
                raise ValueError(f"Claim {claim_id} not found")
            
            # Build evolution graph
            visited = set()
            evolution_graph = {
                "root": claim_id,
                "nodes": [],
                "edges": [],
            }
            
            # BFS to find related claims
            queue = [(claim_id, 0)]  # (claim_id, hop_count)
            
            while queue and len(evolution_graph["nodes"]) < 50:  # Limit graph size
                current_id, hop = queue.pop(0)
                
                if current_id in visited or hop >= max_hops:
                    continue
                
                visited.add(current_id)
                
                # Get claim data
                claim_data = self.qdrant.get_claim_by_id(current_id)
                if claim_data:
                    evolution_graph["nodes"].append({
                        "id": current_id,
                        "payload": claim_data["payload"],
                        "hop_distance": hop,
                    })
                    
                    # Find related claims
                    related = self.qdrant.get_related_claims(current_id, limit=5)
                    
                    for rel in related:
                        rel_id = rel["id"]
                        
                        # Add edge
                        evolution_graph["edges"].append({
                            "from": current_id,
                            "to": rel_id,
                            "similarity": rel["score"],
                            "relationship": self._determine_relationship(
                                claim_data["payload"],
                                rel["payload"]
                            ),
                        })
                        
                        # Add to queue
                        if rel_id not in visited:
                            queue.append((rel_id, hop + 1))
            
            return evolution_graph
            
        except Exception as e:
            logger.error(f"Failed to trace evolution path: {e}")
            raise
    
    def _determine_relationship(
        self,
        claim1: Dict[str, Any],
        claim2: Dict[str, Any],
    ) -> str:
        """Determine the relationship between two claims."""
        # Check if they're on the same platform
        same_platform = claim1.get("platform") == claim2.get("platform")
        
        # Check media type transformation
        media1 = claim1.get("media_type")
        media2 = claim2.get("media_type")
        
        if media1 == media2:
            if same_platform:
                return "duplicate_same_platform"
            else:
                return "cross_platform_duplicate"
        else:
            return f"media_transformation_{media1}_to_{media2}"
    
    def cross_modal_search(
        self,
        text: Optional[str] = None,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search across all modalities simultaneously.
        
        Example: Upload an image and find related text claims.
        """
        try:
            # Generate multimodal embedding
            embedding, transcription = self.embedder.embed_multimodal(
                text=text,
                image=image_path,
                audio_path=audio_path,
            )
            
            # Search across all media types
            results = self.qdrant.search_claims(
                query_vector=embedding,
                limit=limit,
            )
            
            # Annotate with cross-modal matches
            for result in results:
                result_media = result["payload"]["media_type"]
                
                if text and result_media in ["audio", "text"]:
                    result["cross_modal_note"] = "Text query matched audio/text content"
                elif image_path and result_media == "image":
                    result["cross_modal_note"] = "Image query matched similar image"
                elif (text or audio_path) and result_media == "image":
                    result["cross_modal_note"] = "Text/audio query matched image caption or metadata"
            
            return results
            
        except Exception as e:
            logger.error(f"Cross-modal search failed: {e}")
            raise


# Global instance
hybrid_search = HybridSearchService()
