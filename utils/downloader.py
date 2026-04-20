import os
import requests
import zipfile
from datetime import datetime

DOWNLOAD_BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

def download_image_chunked(product_id, product_name, access_token, output_dir="../data"):
    """
    Downloads a 1GB+ Sentinel-1 file in chunks to prevent RAM crashes.
    """
    # Ensure the data directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # CDSE download endpoint format
    download_url = f"{DOWNLOAD_BASE_URL}({product_id})/$value"
    
    # We must pass our authentication token to prove we are allowed to download
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    zip_filepath = os.path.join(output_dir, f"{product_name}.zip")
    
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ⬇️ Starting download for: {product_name}")
    print(f"Saving to: {zip_filepath}")
    
    # stream=True is the most important part. It prevents loading the whole file into RAM.
    with requests.get(download_url, headers=headers, stream=True) as response:
        if response.status_code != 200:
            raise Exception(f"❌ Download failed: {response.status_code} - {response.text}")
        
        # Open a local file in write-binary ('wb') mode
        with open(zip_filepath, 'wb') as file:
            # Download in 8MB chunks (8192 * 1024 bytes)
            for chunk in response.iter_content(chunk_size=8388608): 
                if chunk: # Filter out keep-alive new chunks
                    file.write(chunk)
                    
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ✅ Download complete.")
    return zip_filepath

def extract_safe_zip(zip_filepath, extract_to="../data"):
    """
    Extracts the downloaded .zip file to reveal the .SAFE folder.
    """
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] 📦 Extracting {zip_filepath}...")
    
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            # Dynamically get the root folder name directly from the zip contents
            extracted_items = zip_ref.namelist()
            safe_folder_name = extracted_items[0].split('/')[0]
            
            zip_ref.extractall(extract_to)
            
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ✅ Extraction complete.")
        
        # Once extracted, we delete the .zip file to save hard drive space
        os.remove(zip_filepath)
        print("🗑️ Deleted original .zip file to save space.")
        
        # Build the path using the dynamically retrieved folder name
        safe_folder_path = os.path.join(extract_to, safe_folder_name)
        
        return safe_folder_path
        
    except zipfile.BadZipFile:
        raise Exception("❌ Extraction failed: The downloaded zip file is corrupted.")

# --- TEST EXECUTION ---
if __name__ == "__main__":
    # To test this safely without downloading 1GB, we will just print the logic.
    # In reality, you would pass the ID and token from Stage 7 here.
    
    print("--- DOWNLOADER MODULE LOADED ---")
    print("Functions available: download_image_chunked(), extract_safe_zip()")
    print("Ready to integrate into main orchestrator.")