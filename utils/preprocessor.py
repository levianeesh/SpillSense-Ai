import os
import glob
import rasterio
from rasterio.transform import from_gcps
import numpy as np
from scipy.ndimage import median_filter

def process_sar_image(safe_folder_path):
    """
    Extracts the VV polarization TIFF, applies a median filter to reduce speckle,
    normalizes the array for AI inference, and safely extracts GCP coordinates.
    """
    print(f"\n[PREPROCESSOR] ⚙️ Starting pipeline on: {os.path.basename(safe_folder_path)}")
    
    measurement_dir = os.path.join(safe_folder_path, "measurement")
    if not os.path.exists(measurement_dir):
        raise FileNotFoundError(f"Measurement directory not found in {safe_folder_path}")
        
    vv_files = glob.glob(os.path.join(measurement_dir, "*vv*.tiff"))
    if not vv_files:
        raise FileNotFoundError("No VV polarization TIFF found in the measurement directory.")
        
    target_tiff = vv_files[0]
    print(f"[PREPROCESSOR] 📄 Found target VV TIFF: {os.path.basename(target_tiff)}")
    
    with rasterio.open(target_tiff) as src:
        spatial_profile = src.profile.copy()
        raw_array = src.read(1)
        
        # S1 GRD CRITICAL FIX: Extract CRS and Transform from Ground Control Points
        if spatial_profile.get('crs') is None:
            gcps, gcp_crs = src.gcps
            if gcps:
                print("[PREPROCESSOR] 🌐 Image uses GCPs. Extracting CRS and Affine Transform...")
                spatial_profile['crs'] = gcp_crs
                spatial_profile['transform'] = from_gcps(gcps)
            else:
                spatial_profile['crs'] = 'EPSG:4326' # Absolute Failsafe
                
        print(f"[PREPROCESSOR] 📊 Raw Array Extracted - Shape: {raw_array.shape}, Type: {raw_array.dtype}")
        
        # Create mask and convert to float32
        valid_data_mask = raw_array > 0
        float_array = raw_array.astype(np.float32)
        
        # RAM OPTIMIZATION: Destroy the massive 16-bit raw array immediately
        del raw_array 
        
        print("[PREPROCESSOR] 🧹 Applying 5x5 Median Filter to scrub radar speckle noise...")
        filtered_array = median_filter(float_array, size=5)
        
        # RAM OPTIMIZATION: Destroy the unfiltered float array immediately
        del float_array 
        
        print("[PREPROCESSOR] ⚖️ Normalizing data to 0.0 - 1.0 scale...")
        valid_pixels = filtered_array[valid_data_mask]
        
        if len(valid_pixels) == 0:
            raise ValueError("Image contains no valid data (all zeros).")
            
        min_val = np.percentile(valid_pixels, 1) 
        max_val = np.percentile(valid_pixels, 99)
        
        normalized_array = np.clip(filtered_array, min_val, max_val)
        normalized_array = (normalized_array - min_val) / (max_val - min_val)
        normalized_array[~valid_data_mask] = 0.0
        
        print("[PREPROCESSOR] ✅ Preprocessing complete. Array is now AI-ready.")
        return normalized_array, spatial_profile