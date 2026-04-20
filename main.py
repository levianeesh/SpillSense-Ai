import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

def oil_spill_pipeline_job():
    """
    The main job that executes our entire detection pipeline.
    This will be triggered automatically by the scheduler.
    """
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{current_time}] ⚙️ Waking up! Starting CDSE polling cycle...")
    
    try:
        # TODO: Stage 7 - Call CDSE API here
        # TODO: Stage 8 - Download SAFE file here
        # TODO: Stage 10 - Preprocess array here
        # TODO: Stage 13 - Run U-Net ML model here
        
        # Simulating work taking a few seconds
        time.sleep(2) 
        
        print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}] ✅ Cycle complete. Going back to sleep.\n")
        
    except Exception as e:
        print(f"❌ PIPELINE ERROR: {e}")
        # The scheduler will naturally catch this and try again at the next 15-minute mark.

def start_system():
    """Initializes and boots the polling system."""
    print("🚀 Initializing Near Real-Time Sentinel-1 Polling System...")
    print("⏳ Polling interval set to: 15 minutes.")
    
    # We explicitly use UTC. Never use local time for satellite pipelines.
    scheduler = BlockingScheduler(timezone="UTC")
    
    # Add the pipeline job. 
    # max_instances=1 ensures we don't start a new download if the previous one is still running.
    scheduler.add_job(
        oil_spill_pipeline_job, 
        trigger='interval', 
        minutes=15, 
        id='sar_polling_job',
        max_instances=1 
    )
    
    try:
        # For testing purposes, we manually run the job once immediately 
        # before handing control over to the infinite scheduler loop.
        print("▶️ Running initial startup check...")
        oil_spill_pipeline_job()
        
        print("⏲️ Scheduler started. Waiting for next interval. (Press Ctrl+C to stop)")
        scheduler.start()
        
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Scheduler stopped gracefully. System shutting down.")

if __name__ == "__main__":
    start_system()