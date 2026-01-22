"""
Demo script showcasing VeriFlow capabilities.

This script demonstrates:
1. Submitting claims across different media types
2. Searching for similar claims
3. Generating provenance reports
4. Tracking claim evolution
"""

import asyncio
import requests
import json
from datetime import datetime


API_BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_health_check():
    """Check if the API is running."""
    print_section("Health Check")
    
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200


def demo_submit_text_claim():
    """Demo: Submit a text-based claim."""
    print_section("Demo 1: Submit Text Claim")
    
    claim_text = "COVID-19 vaccines contain microchips for government tracking"
    
    response = requests.post(
        f"{API_BASE_URL}/claims/text",
        params={
            "text": claim_text,
            "platform": "twitter",
            "source_url": "https://twitter.com/example/status/123456",
            "tags": ["covid19", "vaccine", "conspiracy"]
        }
    )
    
    print(f"Submitted claim: {claim_text}")
    print(f"Response: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    return result.get("claim_id")


def demo_search_claims(query):
    """Demo: Search for claims."""
    print_section("Demo 2: Search Claims")
    
    search_data = {
        "query": query,
        "limit": 5
    }
    
    response = requests.post(
        f"{API_BASE_URL}/search",
        json=search_data
    )
    
    print(f"Search query: {query}")
    print(f"Response: {response.status_code}")
    result = response.json()
    
    print(f"\nFound {result.get('total_results', 0)} results:")
    for idx, item in enumerate(result.get("results", []), 1):
        print(f"\n{idx}. Claim ID: {item['id']}")
        print(f"   Similarity Score: {item['score']:.3f}")
        print(f"   Trust Score: {item['payload']['trust_score']:.2f}")
        print(f"   Trust Level: {item['payload']['trust_level']}")
        print(f"   Platform: {item['payload']['platform']}")
        print(f"   Text: {item['payload'].get('original_text', 'N/A')[:100]}...")


def demo_provenance_report(claim_id):
    """Demo: Generate provenance report."""
    print_section("Demo 3: Provenance Report")
    
    response = requests.get(f"{API_BASE_URL}/claims/{claim_id}/provenance")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    report = response.json()
    
    print(f"Provenance Report for Claim: {claim_id}")
    print(f"\n📊 Trust Assessment:")
    print(f"   {report['trust_assessment']}")
    
    print(f"\n📝 Evidence Summary:")
    print(f"   {report['evidence_summary']}")
    
    print(f"\n⏱️  Timeline ({len(report['timeline'])} events):")
    for event in report['timeline'][:5]:  # Show first 5
        print(f"   • {event['timestamp'][:19]}: {event['description']}")
    
    print(f"\n🔗 Related Claims: {len(report['related_claims'])}")
    for related in report['related_claims'][:3]:  # Show first 3
        print(f"   • {related['platform']} ({related['media_type']}): "
              f"Trust {related['trust_score']:.2f}")
    
    print(f"\n💡 Recommendation:")
    print(f"   {report['recommendation']}")


def demo_update_trust_score(claim_id):
    """Demo: Update trust score."""
    print_section("Demo 4: Update Trust Score")
    
    new_score = 0.85  # Mark as verified
    
    response = requests.put(
        f"{API_BASE_URL}/claims/{claim_id}/trust-score",
        params={
            "new_score": new_score,
            "reason": "Verified by multiple authoritative sources"
        }
    )
    
    print(f"Updated trust score to: {new_score}")
    print(f"Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def demo_filtered_search():
    """Demo: Search with filters."""
    print_section("Demo 5: Filtered Search")
    
    search_data = {
        "query": "vaccine safety",
        "platform": "twitter",
        "min_trust_score": 0.6,
        "limit": 3
    }
    
    response = requests.post(
        f"{API_BASE_URL}/search",
        json=search_data
    )
    
    print("Search with filters:")
    print(f"  Query: {search_data['query']}")
    print(f"  Platform: {search_data['platform']}")
    print(f"  Min Trust Score: {search_data['min_trust_score']}")
    
    result = response.json()
    print(f"\nFound {result.get('total_results', 0)} results")
    
    for idx, item in enumerate(result.get("results", []), 1):
        print(f"\n{idx}. {item['payload']['platform']} - Trust: {item['payload']['trust_score']:.2f}")


def run_full_demo():
    """Run the complete demo."""
    print("\n" + "🚀" * 40)
    print("  VeriFlow: Multimodal Digital Trust & Forensic Memory Agent")
    print("  Demo Script")
    print("🚀" * 40)
    
    # Check if API is running
    if not demo_health_check():
        print("\n❌ Error: API is not running. Please start it with:")
        print("   python -m src.main")
        print("   or")
        print("   uvicorn src.main:app --reload")
        return
    
    try:
        # Demo 1: Submit a claim
        claim_id = demo_submit_text_claim()
        
        if not claim_id:
            print("❌ Failed to submit claim")
            return
        
        # Demo 2: Search for claims
        demo_search_claims("vaccine microchip conspiracy")
        
        # Demo 3: Get provenance report
        demo_provenance_report(claim_id)
        
        # Demo 4: Update trust score
        demo_update_trust_score(claim_id)
        
        # Demo 5: Filtered search
        demo_filtered_search()
        
        print_section("Demo Complete! ✅")
        print("You can now:")
        print("  1. Visit http://localhost:8000/docs for interactive API documentation")
        print("  2. Try more queries with different filters")
        print("  3. Upload images or audio files")
        print("  4. Explore the evolution of claims over time")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_full_demo()
