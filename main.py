import time
import os
import shutil
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from utils.roi_handler import load_roi_as_wkt
from utils.cdse_api import get_access_token, build_search_query, execute_search
from utils.downloader import download_image_chunked, extract_safe_zip
from utils.s1_parser import parse_sentinel1_filename, validate_for_ml_pipeline

# Global set to remember processed images to prevent infinite loops
PROCESSED_IDS = set()

def oil_spill_pipeline_job():
    """
    The main job that executes our entire detection pipeline automatically.
    """
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"\n[{current_time}] ⚙️ SYSTEM WAKE! Starting CDSE polling cycle...")
    
    # Define paths
    base_dir = os.path.dirname(__file__)
    roi_path = os.path.join(base_dir, "data", "mumbai_roi.geojson")
    data_dir = os.path.join(base_dir, "data")
    
    try:
        # STEP 1: Get ROI and Auth
        wkt_polygon = load_roi_as_wkt(roi_path)
        token = get_access_token()
        
        # STEP 2: Query CDSE (Look back 24 hours for automated mode)
        query_url = build_search_query(wkt_polygon, hours_back=24)
        found_images = execute_search(token, query_url)
        
        if not found_images:
            print("STANDBY: No new images found in the specified time window.")
            return
            
        target_scene = found_images[0]
        image_id = target_scene['id']
        
        # Check if already processed today
        if image_id in PROCESSED_IDS:
            print(f"SKIP: Image {target_scene['name']} has already been processed today.")
            return
            
        # STEP 3: Validate Metadata
        metadata = parse_sentinel1_filename(target_scene['name'])
        is_valid, validation_msg = validate_for_ml_pipeline(metadata)
        if not is_valid:
            print(f"REJECTED: {validation_msg}")
            PROCESSED_IDS.add(image_id)
            return
            
        print(f"TARGET ACQUIRED: Preparing to process {target_scene['name']}")
        
        # STEP 4: Download and Extract
        zip_path = download_image_chunked(image_id, target_scene['name'], token, output_dir=data_dir)
        safe_path = extract_safe_zip(zip_path, extract_to=data_dir)
        
        # [Future processing steps like ML Inference will go here]
        
        # STEP 5: Cleanup & Memory
        print("CLEANUP: Deleting heavy .SAFE satellite files from server to save space...")
        shutil.rmtree(safe_path)
        
        # Remember this ID so we don't process it again
        PROCESSED_IDS.add(image_id)
        
        print(f"[{datetime.utcnow().strftime('%H:%M:%S UTC')}] ✅ Cycle complete. Going back to sleep.\n")
        
    except Exception as e:
        print(f"❌ PIPELINE ERROR: {e}")
        print("The system will safely retry on the next scheduled interval.")

def start_system():
    """Initializes and boots the polling system."""
    print("🚀 Initializing Near Real-Time Sentinel-1 Polling System...")
    print("⏳ Polling interval set to: 15 minutes.")
    
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        oil_spill_pipeline_job, 
        trigger='interval', 
        minutes=15, 
        id='sar_polling_job',
        max_instances=1 
    )
    
    try:
        print("▶️ Running initial startup check...")
        oil_spill_pipeline_job()
        
        print("⏲️ Scheduler started. Waiting for next interval. (Press Ctrl+C to stop)")
        scheduler.start()
        
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Scheduler stopped gracefully. System shutting down.")

if __name__ == "__main__":
    start_system()