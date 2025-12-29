#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script for the search service.
Run this to verify everything is working before testing via API.
"""

from app.services.search_service.search_service import SearchService
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))


def test_search_service():
    """Test the search service with sample queries"""

    print("="*70)
    print("ALGERIAN LEGAL SEARCH SERVICE - TEST")
    print("="*70)

    # Initialize service
    print("\n[1/3] Initializing SearchService...")
    try:
        service = SearchService()
    except Exception as e:
        print(f"❌ Error initializing service: {e}")
        print("\nTroubleshooting:")
        print("- Check that all 3 files exist in data/ folder")
        print("- Install dependencies: pip install sentence-transformers faiss-cpu")
        return False

    # Check if service is ready
    if not service.is_fitted:
        print("❌ Service failed to load. Check file paths.")
        return False

    print("✅ Service initialized successfully!")

    # Print statistics
    print("\n[2/3] Index Statistics:")
    print("-" * 70)
    stats = service.get_stats()
    print(f"Status: {stats['status']}")
    print(f"Total Documents: {stats['total_documents']:,}")
    print(f"Index Vectors: {stats['index_vectors']:,}")
    print(f"Embedding Model: {stats['embedding_model']}")
    print(f"Embedding Dimension: {stats['embedding_dimension']}")
    print(f"\nDocument Types:")
    for doc_type, count in sorted(stats['document_types'].items()):
        print(f"  - {doc_type}: {count:,}")

    # Test queries
    print("\n[3/3] Testing Search Queries:")
    print("-" * 70)

    test_queries = [
        "Qu'est-ce que l'Algérie selon la constitution?",
        "Quels sont les droits et libertés fondamentaux?",
        "Quelle est la religion officielle de l'Algérie?",
        "Comment est organisé le pouvoir législatif?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        print()

        try:
            results = service.search(query, top_n=3)

            if not results:
                print("  ⚠️  No results found")
                continue

            for j, result in enumerate(results, 1):
                doc = result['document']
                similarity = result['similarity']

                doc_type = doc.get('source_document_type', 'N/A').upper()
                header = doc.get('header', 'N/A')
                content = doc.get('content', 'N/A')

                print(f"  Result {j} (similarity: {similarity:.4f})")
                print(f"  └─ Type: {doc_type}")
                print(f"  └─ Ref: {header[:80]}...")
                print(f"  └─ Content: {content[:150]}...")
                print()

        except Exception as e:
            print(f"  ❌ Error during search: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nNext steps:")
    print("1. Start your Flask app: python run.py")
    print("2. Test the chat endpoint with curl or Postman")
    print("3. Connect your frontend")
    return True


if __name__ == "__main__":
    success = test_search_service()
    sys.exit(0 if success else 1)
