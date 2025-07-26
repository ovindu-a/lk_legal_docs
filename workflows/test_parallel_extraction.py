#!/usr/bin/env python3
"""
Test script to compare sequential vs parallel extraction performance
"""

import time
import sys
from pathlib import Path

# Import both sequential and parallel versions
from folder_traversal import extract_year_data
from parallel_folder_traversal import extract_year_data_parallel


def test_extraction_comparison():
    """Compare performance of sequential vs parallel extraction"""
    
    # Test with a sample year directory - adjust this path as needed
    test_year_dir = "data/gazettes/2024"  # Change this to an actual year directory
    
    if not Path(test_year_dir).exists():
        print(f"Test directory '{test_year_dir}' does not exist.")
        print("Please update the test_year_dir variable to point to a valid year directory.")
        return
    
    print("=" * 60)
    print("EXTRACTION PERFORMANCE COMPARISON")
    print("=" * 60)
    
    # Test sequential extraction
    print("\n1. Testing SEQUENTIAL extraction...")
    print("-" * 40)
    start_time = time.time()
    extract_year_data(test_year_dir)
    sequential_time = time.time() - start_time
    print(f"\nSequential extraction completed in: {sequential_time:.2f} seconds")
    
    # Clean up the data.json file for the parallel test
    data_file = Path(test_year_dir) / "data.json"
    if data_file.exists():
        data_file.unlink()
        print("Cleaned up data.json for parallel test")
    
    # Test parallel extraction
    print("\n2. Testing PARALLEL extraction...")
    print("-" * 40)
    start_time = time.time()
    extract_year_data_parallel(test_year_dir, max_workers=4, max_retries=3)
    parallel_time = time.time() - start_time
    print(f"\nParallel extraction completed in: {parallel_time:.2f} seconds")
    
    # Calculate speedup
    if parallel_time > 0:
        speedup = sequential_time / parallel_time
        print(f"\n{'=' * 60}")
        print(f"RESULTS:")
        print(f"Sequential time: {sequential_time:.2f} seconds")
        print(f"Parallel time: {parallel_time:.2f} seconds")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Time saved: {sequential_time - parallel_time:.2f} seconds ({((sequential_time - parallel_time) / sequential_time * 100):.1f}%)")
        print(f"{'=' * 60}")


def test_retry_logic():
    """Test the retry logic with a single document"""
    from parallel_folder_traversal import extract_single_document
    
    print("\n" + "=" * 60)
    print("TESTING RETRY LOGIC")
    print("=" * 60)
    
    # Find a sample document directory
    sample_doc_dir = None
    for year_dir in Path("data/gazettes").iterdir():
        if year_dir.is_dir():
            for doc_dir in year_dir.iterdir():
                if doc_dir.is_dir() and (doc_dir / "metadata.json").exists():
                    sample_doc_dir = doc_dir
                    break
            if sample_doc_dir:
                break
    
    if not sample_doc_dir:
        print("No sample document directory found for testing")
        return
    
    print(f"\nTesting with document: {sample_doc_dir.name}")
    print("This will attempt extraction with retry logic...")
    
    result = extract_single_document(sample_doc_dir, max_retries=2)
    
    if result:
        print(f"\n✓ Extraction successful!")
        print(f"  Document name: {result['name']}")
        print(f"  Text length: {len(result.get('data', ''))}")
    else:
        print("\n✗ Extraction failed after all retries")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test parallel extraction functionality")
    parser.add_argument("--test", choices=["compare", "retry", "both"], default="both",
                       help="Which test to run")
    
    args = parser.parse_args()
    
    if args.test in ["compare", "both"]:
        test_extraction_comparison()
    
    if args.test in ["retry", "both"]:
        test_retry_logic()