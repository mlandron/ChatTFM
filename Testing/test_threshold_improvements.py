#!/usr/bin/env python3
"""
Test script for threshold improvements in RAG service
Tests the new similarity threshold (0.75), adaptive threshold handling, and context filtering
"""

import os
import sys
import logging
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag_service import RAGConfig, RAGService

def test_threshold_configuration():
    """Test that the new threshold configuration is working"""
    print("\n=== Testing Threshold Configuration ===")
    
    config = RAGConfig()
    
    print(f"Default RPC threshold: {config.default_rpc_threshold}")
    print(f"BM25 score threshold: {config.bm25_score_threshold}")
    print(f"Adaptive threshold enabled: {config.adaptive_threshold_enabled}")
    print(f"Adaptive threshold steps: {config.adaptive_threshold_steps}")
    print(f"Minimum document count: {config.min_document_count}")
    
    # Verify the threshold was updated from 0.2 to 0.75
    assert config.default_rpc_threshold == 0.75, f"Expected 0.75, got {config.default_rpc_threshold}"
    print("✅ Default threshold correctly set to 0.75")

def test_adaptive_threshold():
    """Test adaptive threshold functionality"""
    print("\n=== Testing Adaptive Threshold ===")
    
    config = RAGConfig()
    service = RAGService(config)
    
    # Test query that might need adaptive threshold
    test_queries = [
        "¿Qué es el sistema de pensiones dominicano?",
        "¿Cuáles son los requisitos para jubilarse?"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        
        # Test with adaptive threshold enabled
        result_adaptive = service.query_rag(query)
        
        print(f"  Documents found: {result_adaptive.get('document_count', 0)}")
        print(f"  Unique sources: {result_adaptive.get('unique_sources_count', 0)}")
        print(f"  Confidence score: {result_adaptive.get('confidence_score', 0):.3f}")
        
        if result_adaptive.get('warning'):
            print(f"  ⚠️  Warning: {result_adaptive['warning']}")
        
        # Check if we got a reasonable response
        if result_adaptive.get('document_count', 0) > 0:
            print("  ✅ Found relevant documents")
        else:
            print("  ❌ No documents found")

def test_score_filtering():
    """Test that low-quality documents are being filtered out"""
    print("\n=== Testing Score Filtering ===")
    
    config = RAGConfig()
    service = RAGService(config)
    
    # Test with a specific query
    query = "¿Qué es el sistema de pensiones dominicano?"
    
    # Get the retriever directly to inspect documents
    retriever = service.get_hybrid_retriever()
    if retriever:
        documents = retriever.invoke(query)
        
        print(f"Retrieved {len(documents)} documents")
        
        # Check scores
        for i, doc in enumerate(documents[:5]):  # Show first 5
            score = doc.metadata.get('score', 0)
            retriever_type = doc.metadata.get('retriever_type', 'unknown')
            print(f"  Doc {i+1}: Score={score:.3f}, Type={retriever_type}")
            
            # Verify scores meet minimum thresholds
            if retriever_type == 'vector':
                assert score >= config.default_rpc_threshold, f"Vector score {score} below threshold {config.default_rpc_threshold}"
            elif retriever_type == 'bm25':
                assert score >= config.bm25_score_threshold, f"BM25 score {score} below threshold {config.bm25_score_threshold}"
        
        print("✅ All document scores meet minimum thresholds")

def test_no_documents_handling():
    """Test graceful handling when no relevant documents are found"""
    print("\n=== Testing No Documents Handling ===")
    
    config = RAGConfig()
    service = RAGService(config)
    
    # Test with a very specific query that might not have matches
    obscure_queries = [
        "¿Cómo hacer una torta de chocolate con ingredientes específicos de la República Dominicana?",
        "¿Cuál es el horario de vuelos de Santo Domingo a Nueva York?",
        "¿Dónde puedo comprar ropa de marca en Santiago?"
    ]
    
    for query in obscure_queries:
        print(f"\nTesting obscure query: {query}")
        
        result = service.query_rag(query)
        
        print(f"  Answer: {result.get('answer', '')[:100]}...")
        print(f"  Documents: {result.get('document_count', 0)}")
        print(f"  Warning: {result.get('warning', 'None')}")
        
        # Should handle gracefully without crashing
        assert 'error' not in result or not result['error'], f"Unexpected error: {result.get('error')}"
        print("  ✅ Handled gracefully")

def test_confidence_scoring():
    """Test that confidence scores are being calculated correctly"""
    print("\n=== Testing Confidence Scoring ===")
    
    config = RAGConfig()
    service = RAGService(config)
    
    # Test with a good query
    query = "¿Qué dice la ley 87-01 sobre el régimen contributivo?"
    
    result = service.query_rag(query)
    
    confidence = result.get('confidence_score', 0)
    doc_count = result.get('document_count', 0)
    
    print(f"Query: {query}")
    print(f"Confidence score: {confidence:.3f}")
    print(f"Document count: {doc_count}")
    
    if doc_count > 0:
        # Confidence should be between 0 and 1
        assert 0 <= confidence <= 1, f"Confidence score {confidence} out of range [0,1]"
        print("✅ Confidence score is within valid range")
    else:
        print("⚠️  No documents found, confidence score not applicable")

def main():
    """Run all threshold improvement tests"""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing RAG Service Threshold Improvements")
    print("=" * 50)
    
    try:
        test_threshold_configuration()
        test_adaptive_threshold()
        test_score_filtering()
        test_no_documents_handling()
        test_confidence_scoring()
        
        print("\n" + "=" * 50)
        print("✅ All threshold improvement tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 