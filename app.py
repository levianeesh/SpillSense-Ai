import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import functional utility modules
from utils.cdse_api import get_access_token, build_search_query, execute_search
from utils.downloader import download_image_chunked, extract_safe_zip
from utils.s1_parser import parse_sentinel1_filename, validate_for_ml_pipeline

# Import the Data Preparation Pipeline
from utils.preprocessor import process_sar_image
from utils.land_mask import apply_land_mask

app = FastAPI(title="SpillSense-Ai Live API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RoiPayload(BaseModel):
    wkt: str

@app.post("/api/trigger-pipeline")
async def trigger_pipeline(payload: RoiPayload):
    wkt_string = payload.wkt
    
    if not wkt_string.startswith("POLYGON"):
        raise HTTPException(status_code=400, detail="Invalid WKT geometry format.")
        
    print(f"\n[SERVER] 📥 Received target coordinates: {wkt_string}")
    
    try:
        # 1. Authenticate & Search
        token = get_access_token()
        print("[SERVER] 🔍 Querying Copernicus Data Space Ecosystem...")
        query_url = build_search_query(wkt_string, hours_back=168)
        found_images = execute_search(token, query_url)
        
        if not found_images:
            return {
                "status": "success",
                "message": "Region scanned successfully. No new Sentinel-1 acquisitions found in the last 7 days.",
                "data_found": False
            }
            
        target_scene = found_images[0]
        print(f"[SERVER] 📦 Target acquired! Validating: {target_scene['name']}")
        
        # 2. Validate Metadata
        metadata = parse_sentinel1_filename(target_scene['name'])
        is_valid, validation_msg = validate_for_ml_pipeline(metadata)
        
        if not is_valid:
            return {
                "status": "rejected",
                "message": f"Scene rejected during metadata check: {validation_msg}",
                "data_found": False
            }
            
        print("[SERVER] ✅ Scene passes ML constraints. Starting chunked download...")
        
        # 3. Download & Extract
        zip_path = download_image_chunked(
            product_id=target_scene["id"],
            product_name=target_scene["name"],
            access_token=token,
            output_dir="./data"
        )
        safe_path = extract_safe_zip(zip_path, extract_to="./data")
        
        # 4. --- EXECUTE PREPROCESSING PIPELINE ---
        print("\n[SERVER] 🛠️ Initiating Data Preparation Pipeline...")
        ai_ready_array, spatial_profile = process_sar_image(safe_path)
        
        # 5. --- APPLY LAND MASK ---
        ocean_only_array = apply_land_mask(ai_ready_array, spatial_profile)
        
        return {
            "status": "success",
            "message": f"Pipeline completed. Data downloaded, scrubbed, and masked.\nFinal AI-Ready Tensor Shape: {ocean_only_array.shape}.",
            "data_found": True,
            "scene_name": target_scene["name"],
            "storage_path": safe_path
        }
        
    except Exception as e:
        print(f"\n[SERVER] ❌ CRITICAL FAILURE: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)