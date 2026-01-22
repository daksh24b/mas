from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
import numpy as np

from src.models import (
    ClaimMetadata,
    EvidenceEntry,
    TrustLevel,
    MediaType,
    ClaimEvolution,
)
from src.config import settings


class TrustScoreCalculator:
    """Calculate and update trust scores for claims based on evidence."""
    
    def __init__(self):
        """Initialize trust score calculator with threshold values."""
        self.trust_thresholds = {
            "high": settings.trust_score_high,
            "medium": settings.trust_score_medium,
            "low": settings.trust_score_low,
        }
    
    def calculate_initial_score(
        self,
        source_credibility: float = 0.5,
        platform_reliability: float = 0.5,
    ) -> float:
        """
        Calculate initial trust score for a new claim.
        
        Args:
            source_credibility: Credibility score of the source (0-1)
            platform_reliability: Reliability score of the platform (0-1)
        
        Returns:
            Initial trust score (0-1)
        """
        # Weighted average of source and platform
        initial_score = (source_credibility * 0.6) + (platform_reliability * 0.4)
        return max(0.0, min(1.0, initial_score))
    
    def update_score_with_evidence(
        self,
        current_score: float,
        evidence_list: List[EvidenceEntry],
        decay_factor: float = 0.95,
    ) -> float:
        """
        Update trust score based on new evidence.
        
        Args:
            current_score: Current trust score
            evidence_list: List of evidence entries
            decay_factor: Time decay factor for older evidence
        
        Returns:
            Updated trust score
        """
        if not evidence_list:
            return current_score
        
        # Sort evidence by timestamp (newest first)
        sorted_evidence = sorted(
            evidence_list,
            key=lambda e: e.timestamp,
            reverse=True
        )
        
        # Calculate evidence impact
        supporting_weight = 0.0
        refuting_weight = 0.0
        
        for idx, evidence in enumerate(sorted_evidence):
            # Apply time decay (newer evidence has more weight)
            time_weight = decay_factor ** idx
            evidence_impact = evidence.credibility_score * time_weight
            
            if evidence.is_supporting:
                supporting_weight += evidence_impact
            else:
                refuting_weight += evidence_impact
        
        # Normalize weights
        total_weight = supporting_weight + refuting_weight
        if total_weight > 0:
            support_ratio = supporting_weight / total_weight
        else:
            support_ratio = 0.5
        
        # Update score with momentum (current score has some inertia)
        momentum = 0.3
        new_score = (current_score * momentum) + (support_ratio * (1 - momentum))
        
        return max(0.0, min(1.0, new_score))
    
    def calculate_temporal_decay(
        self,
        current_score: float,
        last_updated: datetime,
        decay_rate: float = 0.01,
    ) -> float:
        """
        Apply temporal decay to trust score for claims without recent updates.
        
        Args:
            current_score: Current trust score
            last_updated: Last update timestamp
            decay_rate: Daily decay rate
        
        Returns:
            Decayed trust score
        """
        days_since_update = (datetime.utcnow() - last_updated).days
        
        if days_since_update == 0:
            return current_score
        
        # Apply exponential decay towards neutral (0.5)
        decay_factor = (1 - decay_rate) ** days_since_update
        neutral_score = 0.5
        
        decayed_score = neutral_score + (current_score - neutral_score) * decay_factor
        return max(0.0, min(1.0, decayed_score))
    
    def determine_trust_level(self, trust_score: float) -> TrustLevel:
        """
        Determine trust level category based on numerical score.
        
        Args:
            trust_score: Numerical trust score (0-1)
        
        Returns:
            TrustLevel enum value
        """
        if trust_score >= 0.85:
            return TrustLevel.VERIFIED
        elif trust_score >= self.trust_thresholds["high"]:
            return TrustLevel.LIKELY_TRUE
        elif trust_score >= self.trust_thresholds["medium"]:
            return TrustLevel.UNCERTAIN
        elif trust_score >= 0.2:
            return TrustLevel.LIKELY_FALSE
        else:
            return TrustLevel.DEBUNKED
    
    def calculate_credibility_boost(
        self,
        verification_sources: List[str],
        official_sources: List[str] = None,
    ) -> float:
        """
        Calculate credibility boost based on verification sources.
        
        Args:
            verification_sources: List of sources that verified the claim
            official_sources: List of official/authoritative sources
        
        Returns:
            Credibility boost factor (0-0.3)
        """
        if official_sources is None:
            official_sources = []
        
        boost = 0.0
        
        # Boost for multiple independent verifications
        verification_boost = min(len(verification_sources) * 0.05, 0.15)
        boost += verification_boost
        
        # Additional boost for official sources
        official_boost = min(len(official_sources) * 0.075, 0.15)
        boost += official_boost
        
        return min(boost, 0.3)


class MemoryManager:
    """Manage the temporal memory and evolution of claims."""
    
    def __init__(self):
        """Initialize memory manager."""
        self.trust_calculator = TrustScoreCalculator()
    
    def build_claim_evolution(
        self,
        original_claim: ClaimMetadata,
        related_claims: List[ClaimMetadata],
        evidence_trail: List[EvidenceEntry],
    ) -> ClaimEvolution:
        """
        Build a comprehensive evolution history for a claim.
        
        Args:
            original_claim: The original claim metadata
            related_claims: Related claims found through vector search
            evidence_trail: Evidence entries associated with the claim
        
        Returns:
            ClaimEvolution object with full history
        """
        # Build trust score history
        trust_history = self._build_trust_history(
            original_claim,
            evidence_trail
        )
        
        return ClaimEvolution(
            claim_id=original_claim.claim_id,
            original_claim=original_claim,
            related_claims=related_claims,
            evidence_trail=evidence_trail,
            trust_score_history=trust_history,
        )
    
    def _build_trust_history(
        self,
        claim: ClaimMetadata,
        evidence_trail: List[EvidenceEntry],
    ) -> List[Dict[str, Any]]:
        """Build the historical trust score progression."""
        history = []
        
        # Add initial state
        history.append({
            "timestamp": claim.timestamp.isoformat(),
            "trust_score": self.trust_calculator.calculate_initial_score(),
            "trust_level": "uncertain",
            "event": "Claim first observed",
        })
        
        # Sort evidence by timestamp
        sorted_evidence = sorted(evidence_trail, key=lambda e: e.timestamp)
        
        # Track score evolution with each piece of evidence
        current_score = claim.trust_score
        
        for evidence in sorted_evidence:
            # Calculate new score with this evidence
            current_score = self.trust_calculator.update_score_with_evidence(
                current_score,
                [evidence],
            )
            
            trust_level = self.trust_calculator.determine_trust_level(current_score)
            
            history.append({
                "timestamp": evidence.timestamp.isoformat(),
                "trust_score": current_score,
                "trust_level": trust_level.value,
                "event": f"{'Supporting' if evidence.is_supporting else 'Refuting'} evidence added",
                "evidence_id": evidence.evidence_id,
            })
        
        return history
    
    def generate_evidence_summary(
        self,
        evidence_trail: List[EvidenceEntry],
    ) -> str:
        """Generate a human-readable summary of evidence."""
        if not evidence_trail:
            return "No evidence available for this claim."
        
        supporting = [e for e in evidence_trail if e.is_supporting]
        refuting = [e for e in evidence_trail if not e.is_supporting]
        
        summary = f"Evidence Summary:\n"
        summary += f"- Total pieces of evidence: {len(evidence_trail)}\n"
        summary += f"- Supporting evidence: {len(supporting)}\n"
        summary += f"- Refuting evidence: {len(refuting)}\n\n"
        
        if supporting:
            summary += "Key supporting sources:\n"
            for e in supporting[:3]:  # Top 3
                summary += f"  • {e.media_type.value} from {e.source_url or 'unknown source'} "
                summary += f"(credibility: {e.credibility_score:.2f})\n"
        
        if refuting:
            summary += "\nKey refuting sources:\n"
            for e in refuting[:3]:  # Top 3
                summary += f"  • {e.media_type.value} from {e.source_url or 'unknown source'} "
                summary += f"(credibility: {e.credibility_score:.2f})\n"
        
        return summary
    
    def generate_timeline(
        self,
        claim: ClaimMetadata,
        evidence_trail: List[EvidenceEntry],
        related_claims: List[ClaimMetadata],
    ) -> List[Dict[str, Any]]:
        """Generate a chronological timeline of claim evolution."""
        timeline = []
        
        # Add original claim
        timeline.append({
            "timestamp": claim.timestamp.isoformat(),
            "type": "claim_first_seen",
            "description": f"Claim first appeared on {claim.platform.value}",
            "media_type": claim.media_type.value,
        })
        
        # Add evidence entries
        for evidence in sorted(evidence_trail, key=lambda e: e.timestamp):
            timeline.append({
                "timestamp": evidence.timestamp.isoformat(),
                "type": "evidence_added",
                "description": f"{'Supporting' if evidence.is_supporting else 'Refuting'} evidence found",
                "media_type": evidence.media_type.value,
                "source": evidence.source_url,
            })
        
        # Add related claims
        for related in related_claims:
            timeline.append({
                "timestamp": related.timestamp.isoformat(),
                "type": "related_claim",
                "description": f"Similar claim found on {related.platform.value}",
                "media_type": related.media_type.value,
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline


# Global instances
trust_calculator = TrustScoreCalculator()
memory_manager = MemoryManager()
