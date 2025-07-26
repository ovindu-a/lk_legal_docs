import os
import json
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Optional
import time
from functools import partial

# Add the parent directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_extraction_v2 import TextExtractionService, ExtractionMethod
service = TextExtractionService()


def extract_single_document(doc_dir: Path, max_retries: int = 3) -> Optional[Dict]:
    """
    Extract data from a single document directory with retry logic.
    
    Args:
        doc_dir: Path to the document directory
        max_retries: Maximum number of retry attempts if extraction fails
        
    Returns:
        Dictionary with extracted data or None if all attempts fail
    """
    metadata_file = doc_dir / "metadata.json"
    
    if not metadata_file.exists():
        print(f"✗ No metadata.json found in {doc_dir.name}")
        return None
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing metadata.json in {doc_dir.name}: {e}")
        return None
    except Exception as e:
        print(f"✗ Error reading metadata.json in {doc_dir.name}: {e}")
        return None
    
    url = metadata.get("lang_to_source_url", {}).get("en", "")
    if not url:
        print(f"✗ No English URL found in {doc_dir.name}")
        return None
    
    # Initialize service for this process
    
    # Retry logic for extraction
    for attempt in range(max_retries):
        try:
            result = service.extract_from_url(
                url,
                method=ExtractionMethod.PYPDF2,
                prompt="Extract tables and summarize key points"
            )
            
            print(type(result), result.success, result.text, result.error)
            
            if result.success:
                # Extract the required properties
                print(type(result.text), len(result.text))
                
                entry = {
                    "name": metadata.get("id", doc_dir.name),
                    "lang_to_source_url": metadata.get("lang_to_source_url", {}),
                    "data": result.text,  # Use the extracted text
                }
                
                print(f"✓ Extracted data from {doc_dir.name} (attempt {attempt + 1})")
                return entry
            else:
                print(f"⚠ Extraction failed for {doc_dir.name} (attempt {attempt + 1}): {result.error}")
                
        except Exception as e:
            print(f"⚠ Error extracting from {doc_dir.name} (attempt {attempt + 1}): {e}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1, 2, 4 seconds
            print(f"  Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    print(f"✗ Failed to extract data from {doc_dir.name} after {max_retries} attempts")
    return None


def extract_year_data_parallel(year_dir_path: str, max_workers: Optional[int] = None, max_retries: int = 3):
    """
    Extracts data from all subdirectories in a year directory using parallel processing.
    Creates a consolidated data.json file with retry logic for failed extractions.
    
    Args:
        year_dir_path: Path to the year directory
        max_workers: Maximum number of worker processes (None = number of CPUs)
        max_retries: Maximum number of retry attempts for failed extractions
    """
    year_dir = Path(year_dir_path)
    
    # Check if the year directory exists
    if not year_dir.exists():
        print(f"Error: Year directory '{year_dir_path}' does not exist")
        return
    
    if not year_dir.is_dir():
        print(f"Error: '{year_dir_path}' is not a directory")
        return
    
    print(f"\nExtracting data from year directory (parallel): {year_dir_path}")
    print("-" * 50)
    
    # Get all subdirectories (document folders) and sort them
    doc_dirs = [d for d in year_dir.iterdir() if d.is_dir()]
    doc_dirs.sort()
    
    if not doc_dirs:
        print(f"No document directories found in {year_dir.name}")
        return
    
    print(f"Found {len(doc_dirs)} document directories to process")
    print(f"Using {max_workers or 'default'} worker processes")
    print(f"Max retries per document: {max_retries}")
    print()
    
    extracted_data = []
    failed_dirs = []
    
    # Create partial function with max_retries
    extract_func = partial(extract_single_document, max_retries=max_retries)
    
    # Process documents in parallel
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_dir = {executor.submit(extract_func, doc_dir): doc_dir 
                        for doc_dir in doc_dirs}
        
        # Process completed tasks
        for future in as_completed(future_to_dir):
            doc_dir = future_to_dir[future]
            try:
                result = future.result()
                if result:
                    extracted_data.append(result)
                else:
                    failed_dirs.append(doc_dir.name)
            except Exception as e:
                print(f"✗ Unexpected error processing {doc_dir.name}: {e}")
                failed_dirs.append(doc_dir.name)
    
    elapsed_time = time.time() - start_time
    
    # Sort extracted data by name for consistency
    extracted_data.sort(key=lambda x: x.get('name', ''))
    
    # Create the consolidated data.json file in the year directory
    output_file = year_dir / "data.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successfully created {output_file}")
        print(f"  Total entries: {len(extracted_data)}")
        print(f"  Failed extractions: {len(failed_dirs)}")
        print(f"  Time elapsed: {elapsed_time:.2f} seconds")
        print(f"  Average time per document: {elapsed_time / len(doc_dirs):.2f} seconds")
        
        if failed_dirs:
            print(f"\nFailed to extract from the following directories:")
            for dir_name in failed_dirs:
                print(f"  - {dir_name}")
        
    except Exception as e:
        print(f"✗ Error creating data.json: {e}")


def traverse_folders_parallel(folder_name: str, max_workers: Optional[int] = None, max_retries: int = 3):
    """
    Traverses through the specified folder and extracts data from each year directory using parallel processing.
    Creates data.json files in each year directory with consolidated metadata.
    
    Args:
        folder_name: Name of the folder to traverse ('gazettes', 'bills', or 'acts')
        max_workers: Maximum number of worker processes (None = number of CPUs)
        max_retries: Maximum number of retry attempts for failed extractions
    """
    # Define the base data directory
    data_dir = Path("data")
    target_dir = data_dir / folder_name
    
    # Check if the folder exists
    if not target_dir.exists():
        print(f"Error: Folder '{folder_name}' does not exist in {data_dir}")
        return
    
    if not target_dir.is_dir():
        print(f"Error: '{folder_name}' is not a directory")
        return
    
    print(f"\nTraversing folder (parallel mode): {folder_name}")
    print("=" * 50)
    
    # Get all subdirectories (year folders) and sort them
    year_dirs = [d for d in target_dir.iterdir() if d.is_dir()]
    year_dirs.sort()
    
    if not year_dirs:
        print(f"No subdirectories found in {folder_name}")
        return
    
    print(f"Found {len(year_dirs)} year directories:")
    
    total_start_time = time.time()
    
    for year_dir in year_dirs:
        extract_year_data_parallel(str(year_dir), max_workers=max_workers, max_retries=max_retries)
    
    total_elapsed_time = time.time() - total_start_time
    print(f"\n{'=' * 50}")
    print(f"Total processing time: {total_elapsed_time:.2f} seconds")
    print(f"Average time per year: {total_elapsed_time / len(year_dirs):.2f} seconds")


def main():
    """Main function to traverse through all specified folders using parallel processing."""
    import multiprocessing
    
    # You can adjust these parameters
    # max_workers = multiprocessing.cpu_count()  # Use all available CPUs
    max_workers = 3
    max_retries = 3  # Number of retry attempts for failed extractions
    
    folders_to_traverse = ['gazettes']
    
    print(f"Starting parallel extraction with {max_workers} workers")
    print(f"Retry attempts for failed extractions: {max_retries}")
    
    for folder in folders_to_traverse:
        traverse_folders_parallel(folder, max_workers=max_workers, max_retries=max_retries)


if __name__ == "__main__":
    main()