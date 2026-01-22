# VeriFlow Architecture Diagram

## System Architecture (High-Level)

```
┌───────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Web App   │  │  Mobile App │  │     CLI     │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼─────────────────┼─────────────────┼────────────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                      FASTAPI REST API                             │
│                    (Port 8000)                                    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                           │  │
│  │                                                           │  │
│  │  POST /claims/text      │  Submit text claim            │  │
│  │  POST /claims/image     │  Submit image claim           │  │
│  │  POST /claims/audio     │  Submit audio claim           │  │
│  │  POST /search           │  Hybrid search                │  │
│  │  GET  /claims/{id}      │  Get claim details            │  │
│  │  GET  /claims/{id}/     │  Generate provenance          │  │
│  │       provenance        │  report                       │  │
│  │  PUT  /claims/{id}/     │  Update trust score           │  │
│  │       trust-score       │                               │  │
│  │  GET  /health           │  Health check                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Embedding Service                              │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │     CLIP     │  │   Whisper    │  │  Sentence    │   │ │
│  │  │   (512D)     │  │   (Audio→    │  │ Transformers │   │ │
│  │  │ Image+Text   │  │   Text)      │  │   (384D)     │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  │                                                             │ │
│  │  embed_text()  │  embed_image()  │  embed_audio()        │ │
│  │  embed_multimodal() │ compute_similarity()                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Trust Score Service                            │ │
│  │                                                             │ │
│  │  • calculate_initial_score()                               │ │
│  │  • update_score_with_evidence()                            │ │
│  │  • calculate_temporal_decay()                              │ │
│  │  • determine_trust_level()                                 │ │
│  │  • calculate_credibility_boost()                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Memory Manager                                 │ │
│  │                                                             │ │
│  │  • build_claim_evolution()                                 │ │
│  │  • generate_evidence_summary()                             │ │
│  │  • generate_timeline()                                     │ │
│  │  • build_trust_history()                                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Hybrid Search Service                          │ │
│  │                                                             │ │
│  │  • search_with_reasoning()                                 │ │
│  │  • find_claim_evolution_path()                             │ │
│  │  • cross_modal_search()                                    │ │
│  │  • build_reasoning_chain()                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────┬───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                   QDRANT VECTOR DATABASE                          │
│                        (Port 6333)                                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           Collection: veriflow_claims                       │ │
│  │                                                             │ │
│  │  Vector Configuration:                                      │ │
│  │  • Size: 512 dimensions (CLIP)                             │ │
│  │  • Distance: Cosine similarity                             │ │
│  │                                                             │ │
│  │  Payload Fields:                                            │ │
│  │  • claim_id (str)                                          │ │
│  │  • media_type (indexed) → text|image|audio|video          │ │
│  │  • platform (indexed) → twitter|facebook|instagram|...    │ │
│  │  • trust_score (indexed) → 0.0-1.0                        │ │
│  │  • trust_level (indexed) → verified|uncertain|debunked    │ │
│  │  • timestamp (indexed) → datetime                         │ │
│  │  • verification_count (int)                               │ │
│  │  • supporting_evidence_count (int)                        │ │
│  │  • refuting_evidence_count (int)                          │ │
│  │  • last_updated (datetime)                                │ │
│  │  • original_text (str)                                    │ │
│  │  • transcription (str)                                    │ │
│  │  • tags (list[str])                                       │ │
│  │                                                             │ │
│  │  Operations:                                                │ │
│  │  • insert_claim() - Add new claim vector                  │ │
│  │  • search_claims() - Hybrid search (vector + filters)     │ │
│  │  • update_trust_score() - Update payload without reindex  │ │
│  │  • get_related_claims() - Find similar vectors            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow: Submit Image Claim

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. User uploads suspicious image                                │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. POST /claims/image                                            │
│    • File: suspicious_image.jpg                                  │
│    • Platform: instagram                                         │
│    • Caption: "Breaking news!"                                   │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. Embedding Service                                             │
│    • Load image with PIL                                         │
│    • Process with CLIP                                           │
│    • Generate 512D embedding                                     │
│    • If caption: combine image + text embedding                  │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. Trust Service                                                 │
│    • Calculate initial trust score (0.5)                         │
│    • Determine trust level: UNCERTAIN                            │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. Qdrant Service                                                │
│    • Create point with UUID                                      │
│    • Store vector (512D)                                         │
│    • Store payload (metadata)                                    │
│    • Insert into collection                                      │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. Response to user                                              │
│    {                                                             │
│      "claim_id": "abc-123-def",                                 │
│      "trust_score": 0.5,                                        │
│      "trust_level": "uncertain"                                 │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow: Cross-Modal Search

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. User searches for "vaccine microchip"                         │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. POST /search                                                  │
│    {                                                             │
│      "query": "vaccine microchip",                              │
│      "limit": 10                                                │
│    }                                                             │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. Embedding Service                                             │
│    • Generate CLIP text embedding (512D)                         │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. Qdrant Search                                                 │
│    • Vector similarity search                                    │
│    • Returns top 10 most similar claims                          │
│    • Includes ALL media types:                                   │
│      - Text posts mentioning vaccine chips                       │
│      - Images of vaccine/microchip graphics                      │
│      - Audio transcripts discussing topic                        │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. Hybrid Search Service                                         │
│    • Build reasoning chains for each result                      │
│    • Calculate reasoning scores                                  │
│    • Re-rank results                                             │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. Response with reasoning                                       │
│    {                                                             │
│      "results": [                                                │
│        {                                                         │
│          "id": "claim-001",                                      │
│          "score": 0.89,                                          │
│          "media_type": "text",                                   │
│          "trust_score": 0.15,                                    │
│          "reasoning": [                                          │
│            "High semantic similarity (0.89)",                    │
│            "Low trust score indicates unreliability",            │
│            "Debunked by fact-checkers"                           │
│          ]                                                       │
│        },                                                        │
│        {                                                         │
│          "id": "claim-002",                                      │
│          "score": 0.82,                                          │
│          "media_type": "image",                                  │
│          "cross_modal_note": "Text query matched image"          │
│        }                                                         │
│      ]                                                           │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
```

## Trust Score Evolution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Day 1: Claim first submitted                                    │
│                                                                 │
│ Instagram Image: "Vaccine contains chips"                      │
│ ├─ Initial trust_score: 0.5 (UNCERTAIN)                        │
│ └─ Store in Qdrant with timestamp                              │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ Day 3: Similar claim found                                      │
│                                                                 │
│ Twitter Text: Same claim, different wording                    │
│ ├─ Vector search finds similarity: 0.87                        │
│ ├─ Link established (same claim_evolution graph)               │
│ └─ No trust score change yet                                   │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ Day 7: Evidence arrives (REFUTING)                             │
│                                                                 │
│ Fact-check article from CDC                                    │
│ ├─ Evidence credibility: 0.95                                  │
│ ├─ Is supporting: false                                        │
│ ├─ Trust Service recalculates:                                 │
│ │   new_score = f(current=0.5, evidence=[refuting_0.95])       │
│ │   new_score = 0.25                                           │
│ ├─ Qdrant set_payload() updates trust_score → 0.25            │
│ └─ Trust level → LIKELY_FALSE                                  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ Day 14: More evidence (REFUTING)                               │
│                                                                 │
│ Multiple authoritative sources debunk                          │
│ ├─ 3 more refuting evidence entries                            │
│ ├─ Trust Service: new_score = 0.12                             │
│ ├─ Qdrant updates: trust_score → 0.12                         │
│ └─ Trust level → DEBUNKED                                      │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ Day 30: Temporal decay                                          │
│                                                                 │
│ No updates for 16 days                                         │
│ ├─ Decay towards neutral (0.5)                                 │
│ ├─ Small increase: 0.12 → 0.15                                │
│ └─ Still DEBUNKED (needs evidence to change significantly)     │
└─────────────────────────────────────────────────────────────────┘
```

## Provenance Report Generation Flow

```
User requests: GET /claims/{id}/provenance
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Qdrant: Get claim by ID                                   │
│    • Retrieve vector + payload                               │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Qdrant: Find related claims                               │
│    • Vector similarity search using claim's vector           │
│    • Returns top 5 most similar claims                       │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Memory Manager: Build evolution                           │
│    • Sort all claims by timestamp                            │
│    • Build timeline of appearances                           │
│    • Track trust score progression                           │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Trust Service: Generate assessment                        │
│    • Analyze current trust score                             │
│    • Generate human-readable explanation                     │
│    • Provide recommendation                                  │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Assemble complete report                                  │
│    • Current status                                          │
│    • Trust assessment                                        │
│    • Evidence summary                                        │
│    • Timeline (chronological events)                         │
│    • Related claims                                          │
│    • Recommendation                                          │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. Return ProvenanceReport                                   │
│    {                                                         │
│      "claim_id": "...",                                      │
│      "trust_assessment": "Debunked (0.15)...",              │
│      "timeline": [                                           │
│        "2025-12-01: First seen on Instagram (image)",       │
│        "2025-12-03: Related claim on Twitter (text)",       │
│        "2025-12-07: Debunked by CDC (evidence)",           │
│      ],                                                      │
│      "recommendation": "Do not share..."                     │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  • Python 3.10+                                            │
│  • FastAPI 0.109 (async API framework)                    │
│  • Pydantic (data validation)                             │
│  • Uvicorn (ASGI server)                                  │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│                    AI/ML Layer                              │
│  • CLIP (openai/clip-vit-base-patch32)                    │
│  • Whisper (base model)                                   │
│  • Sentence Transformers (all-MiniLM-L6-v2)               │
│  • PyTorch                                                │
│  • Transformers library                                   │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│                    Data Layer                               │
│  • Qdrant 1.7+ (vector database)                          │
│  • 512D vectors (CLIP embeddings)                         │
│  • Cosine similarity                                      │
│  • Indexed payload fields                                 │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│                    Deployment Layer                         │
│  • Docker containers                                       │
│  • Docker Compose orchestration                           │
│  • Environment variables (.env)                           │
│  • Health checks                                          │
└─────────────────────────────────────────────────────────────┘
```

---

**Legend:**
- `→` Data flow
- `│` Sequential process
- `┌─┐` Component boundary
- `•` Feature/capability
