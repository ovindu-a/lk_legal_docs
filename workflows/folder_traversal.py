import os
import json
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from src.lld.services.text_extraction_v2 import TextExtractionService, ExtractionMethod
from text_extraction_v2 import TextExtractionService, ExtractionMethod

service = TextExtractionService()



def print_metadata(folder_path):
    """
    Prints the metadata.json file from the specified folder.
    
    Args:
        folder_path (str): Path to the folder containing metadata.json
    """
    # Convert to Path object for better handling
    folder = Path(folder_path)
    metadata_file = folder / "metadata.json"
    
    # Check if the folder exists
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return
    
    if not folder.is_dir():
        print(f"Error: '{folder_path}' is not a directory")
        return
    
    # Check if metadata.json exists
    if not metadata_file.exists():
        print(f"Error: metadata.json not found in '{folder_path}'")
        return
    
    print(f"\nMetadata for folder: {folder_path}")
    print("=" * 60)
    
    try:
        # Read and parse the JSON file
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Pretty print the JSON with indentation
        # print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print(metadata['lang_to_source_url']['en'])
        print('\n')
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in metadata.json: {e}")
    except Exception as e:
        print(f"Error reading metadata.json: {e}")


def extract_year_data(year_dir_path):
    """
    Extracts data from all subdirectories in a year directory and creates a consolidated data.json file.
    Updates data.json after each individual file extraction.
    
    Args:
        year_dir_path (str): Path to the year directory
    """
    year_dir = Path(year_dir_path)
    
    # Check if the year directory exists
    if not year_dir.exists():
        print(f"Error: Year directory '{year_dir_path}' does not exist")
        return
    
    if not year_dir.is_dir():
        print(f"Error: '{year_dir_path}' is not a directory")
        return
    
    print(f"\nExtracting data from year directory: {year_dir_path}")
    print("-" * 50)
    
    # Get all subdirectories (document folders) and sort them
    doc_dirs = [d for d in year_dir.iterdir() if d.is_dir()]
    doc_dirs.sort()
    
    if not doc_dirs:
        print(f"No document directories found in {year_dir.name}")
        return
    
    # Load existing data if data.json already exists
    output_file = year_dir / "data.json"
    extracted_data = []
    
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                extracted_data = json.load(f)
            print(f"Loaded existing data.json with {len(extracted_data)} entries")
        except Exception as e:
            print(f"Warning: Could not load existing data.json: {e}")
            extracted_data = []
    
    for doc_dir in doc_dirs:
        metadata_file = doc_dir / "metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Check if this document already exists in extracted_data
                doc_id = metadata.get("id", doc_dir.name)
                existing_entry = next((item for item in extracted_data if item.get("name") == doc_id), None)
                
                if existing_entry:
                    print(f"⚠ Skipping {doc_dir.name} - already extracted")
                    continue
                
                url = metadata.get("lang_to_source_url", {}).get("en", "")
                
                # data = # Direct Gemini extraction
                result = service.extract_from_url(
                    url,
                    method=ExtractionMethod.PYPDF2,
                    prompt="Extract tables and summarize key points"
                )
                
                print("Printing result" ,type(result.text))   
                
                # Extract the required properties
                entry = {
                    "name": doc_id,
                    "lang_to_source_url": metadata.get("lang_to_source_url", {}),
                    "data": str(result.text),  # Use the extracted text from Gemini
                }
                
                print(url)
                
                extracted_data.append(entry)
                print(f"✓ Extracted data from {doc_dir.name}")
                
                # Update data.json after each successful extraction
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
                    print(f"✓ Updated data.json - Total entries: {len(extracted_data)}")
                except Exception as e:
                    print(f"✗ Error updating data.json: {e}")
                
            except json.JSONDecodeError as e:
                print(f"✗ Error parsing metadata.json in {doc_dir.name}: {e}")
            except Exception as e:
                print(f"✗ Error reading metadata.json in {doc_dir.name}: {e}")
        else:
            print(f"✗ No metadata.json found in {doc_dir.name}")
    
    print(f"\n✓ Extraction complete for {year_dir.name}")
    print(f"  Total entries in data.json: {len(extracted_data)}")


def traverse_year(year_dir, folder_name):
    """
    Traverses through a specific year directory and prints metadata for all document folders.
    
    Args:
        year_dir (Path): Path to the year directory
        folder_name (str): Name of the parent folder ('gazettes', 'bills', or 'acts')
    """
    print(f"\nYear: {year_dir.name}")
    print("-" * 30)
    
    # Get all subdirectories within the year folder (document folders)
    doc_dirs = [d for d in year_dir.iterdir() if d.is_dir()]
    doc_dirs.sort()
    
    if not doc_dirs:
        print(f"No document directories found in {year_dir.name}")
        return
    
    print(f"Found {len(doc_dirs)} document directories:")
    for i, doc_dir in enumerate(doc_dirs, 1):
        print(f"{i:3d}. {doc_dir.name}")
        
        # Print metadata for each document folder
        print_metadata(str(doc_dir))


def traverse_folders(folder_name):
    """
    Traverses through the specified folder and extracts data from each year directory.
    Creates data.json files in each year directory with consolidated metadata.
    
    Args:
        folder_name (str): Name of the folder to traverse ('gazettes', 'bills', or 'acts')
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
    
    print(f"\nTraversing folder: {folder_name}")
    print("=" * 50)
    
    # Get all subdirectories (year folders) and sort them
    year_dirs = [d for d in target_dir.iterdir() if d.is_dir()]
    year_dirs.sort()
    
    if not year_dirs:
        print(f"No subdirectories found in {folder_name}")
        return
    
    print(f"Found {len(year_dirs)} year directories:")
    
    if folder_name == 'gazettes':
        for year_dir in year_dirs[12:]:
            extract_year_data(str(year_dir))
    else:
        for year_dir in year_dirs[6:]:
            extract_year_data(str(year_dir))


def cleanup_data_files():
    """
    Deletes all generated data.json files from year directories in acts, bills, and gazettes folders.
    """
    data_dir = Path("data")
    folders_to_clean = ['acts', 'bills', 'gazettes']
    deleted_files = []
    
    print("Cleaning up generated data.json files...")
    print("=" * 50)
    
    for folder_name in folders_to_clean:
        folder_path = data_dir / folder_name
        
        if not folder_path.exists():
            print(f"Folder '{folder_name}' does not exist, skipping...")
            continue
        
        print(f"\nChecking folder: {folder_name}")
        
        # Get all year directories
        year_dirs = [d for d in folder_path.iterdir() if d.is_dir()]
        
        for year_dir in year_dirs:
            data_file = year_dir / "data.json"
            
            if data_file.exists():
                try:
                    data_file.unlink()  # Delete the file
                    deleted_files.append(str(data_file))
                    print(f"✓ Deleted: {data_file}")
                except Exception as e:
                    print(f"✗ Error deleting {data_file}: {e}")
    
    print(f"\nCleanup completed!")
    print(f"Total files deleted: {len(deleted_files)}")
    
    if deleted_files:
        print("\nDeleted files:")
        for file_path in deleted_files:
            print(f"  - {file_path}")


def main():
    """Main function to traverse through all specified folders."""
    folders_to_traverse = ['acts', 'bills', 'gazettes', 'extra-gazettes']
    
    for folder in folders_to_traverse:
        traverse_folders(folder)


if __name__ == "__main__":
    main() 
