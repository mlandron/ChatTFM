# test_optimized_service.py
import asyncio
import time
import psutil
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rag_service import RAGConfig, RAGService as OptimizedRAGService

async def test_memory_usage():
    """Test memory usage of optimized service"""
    process = psutil.Process(os.getpid())
    
    # Measure initial memory
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Initial memory: {initial_memory:.2f} MB")
    
    # Initialize service
    config = RAGConfig()
    service = OptimizedRAGService(config)
    
    # Measure after initialization
    init_memory = process.memory_info().rss / 1024 / 1024
    print(f"After initialization: {init_memory:.2f} MB")
    print(f"Initialization overhead: {init_memory - initial_memory:.2f} MB")
    
    # Test queries
    queries = [
        "¿Qué es el sistema de pensiones dominicano?",
        "¿Cuáles son los requisitos para jubilarse?",
        "¿Cómo funciona el régimen contributivo?"
    ]
    
    for i, query in enumerate(queries):
        start_time = time.time()
        result = await service.query_rag(query)
        end_time = time.time()
        
        current_memory = process.memory_info().rss / 1024 / 1024
        print(f"Query {i+1}: {end_time - start_time:.2f}s, Memory: {current_memory:.2f} MB")
        print(f"Answer length: {len(result['answer'])} chars")
        print("---")

if __name__ == "__main__":
    asyncio.run(test_memory_usage())