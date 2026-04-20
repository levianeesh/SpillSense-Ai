import os

def parse_sentinel1_filename(filename):
    """
    Parses a standard Sentinel-1 SAFE filename and extracts metadata.
    Example input: S1A_IW_GRDH_1SDV_20260420T013537_20260420T013602_043405_052DF0_9876.SAFE
    """
    # Remove the .SAFE extension for parsing
    clean_name = filename.replace(".SAFE", "")
    parts = clean_name.split("_")
    
    # Check if this is a valid Sentinel-1 filename structure
    if len(parts) < 8 or not parts[0].startswith("S1"):
        raise ValueError(f"Invalid Sentinel-1 filename format: {filename}")

    metadata = {
        "mission": parts[0],              # S1A or S1B
        "beam_mode": parts[1],            # IW (Interferometric Wide) is standard for oceans
        "product_type": parts[2][:3],     # GRD (Ground Range Detected) or SLC
        "resolution": parts[2][3:],       # H (High), M (Medium)
        "processing_level": parts[3][0],  # 1 or 2
        "polarization": parts[3][2:],     # DV (Dual VV/VH) or SV (Single VV)
        "start_time": parts[4],           # e.g., 20260420T013537
        "stop_time": parts[5]
    }
    
    return metadata

def validate_for_ml_pipeline(metadata):
    """
    Ensures the image is valid for our U-Net pipeline.
    We STRICTLY want GRD (Ground Range Detected) images.
    """
    if metadata["product_type"] != "GRD":
        return False, f"Rejected: Need GRD data, but got {metadata['product_type']}."
    
    if metadata["beam_mode"] != "IW":
        return False, f"Rejected: Need IW beam mode, but got {metadata['beam_mode']}."
        
    return True, "Data is valid for AI processing."

# --- TEST EXECUTION ---
if __name__ == "__main__":
    test_file = "S1A_IW_GRDH_1SDV_20260420T013537_20260420T013602_043405_052DF0_9876.SAFE"
    print(f"Analyzing File: {test_file}\n")
    
    try:
        data_meta = parse_sentinel1_filename(test_file)
        for key, value in data_meta.items():
            print(f"{key.upper()}: {value}")
            
        is_valid, msg = validate_for_ml_pipeline(data_meta)
        print(f"\nPIPELINE CHECK: {msg}")
        
    except ValueError as e:
        print(f"Error: {e}")