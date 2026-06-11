# SpillSense-Ai | Near Real-Time Oil Spill Detection Backend

SpillSense-Ai is an automated backend pipeline designed to ingest, process, and analyze Sentinel-1 Synthetic Aperture Radar (SAR) imagery for coastal environmental monitoring. 

This repository contains the data preparation pipeline, the master polling scheduler, and a decoupled FastAPI server with a graphical map interface for rapid Region of Interest (ROI) testing.

## 📁 Project Structure

Ensure your local directory strictly matches this structure to prevent module import errors:

    /SpillSense-Ai
    ├── .env                    # Hidden credentials (not tracked in git)
    ├── app.py                  # FastAPI server for on-demand pipeline triggers
    ├── main.py                 # Master APScheduler for automated 15-minute polling
    ├── map_interface.html      # Leaflet.js graphical ROI builder
    ├── requirements.txt        # Python dependencies
    ├── data/
    │   └── mumbai_roi.geojson  # Static fallback geometry
    └── utils/
        ├── cdse_api.py         # Copernicus Data Space auth and OData querying
        ├── downloader.py       # Chunked streaming and zip extraction
        ├── land_mask.py        # Geographic boundary fetching and array masking
        ├── preprocessor.py     # TIFF extraction, median filtering, and normalization
        ├── roi_handler.py      # GeoJSON to WKT coordinate translation
        └── s1_parser.py        # Metadata validation (GRD/IW enforcement)

## 🚀 Execution Instructions

Follow these steps to spin up the entire backend ecosystem on your local machine. 

### 1. Initial Setup
Clone the repository and install all required heavy geospatial dependencies (FastAPI, Uvicorn, Rasterio, GeoPandas, etc.).

    git clone https://github.com/Spectrae/SpillSense-Ai.git
    cd SpillSense-Ai
    pip install -r requirements.txt

### 2. Configure Credentials
Create a `.env` file in the root of your project folder. The system uses `python-dotenv` to securely load these. Do **not** commit this file.

    CDSE_USERNAME=your_registered_email@example.com
    CDSE_PASSWORD=your_super_secret_password

### 3. Boot the API Server
Start the decoupled FastAPI server. This acts as the listener for spatial queries and executes the downloading and preprocessing scripts.

    uvicorn app:app --reload --host 127.0.0.1 --port 8000

*Wait until the terminal reads `Application startup complete`.*

### 4. Launch the Map Interface (Testing Mode)
With the FastAPI server running in the background, double-click `map_interface.html` to open it in your web browser. 
1. Draw a bounding box over the ocean.
2. Click **Simulate Pipeline Trigger**. 
3. Watch your Python terminal to see the API authenticate, download the chunked `.SAFE` file, extract the VV TIFF, apply the median filter, and mask out the landmasses in real-time.

### 5. Automated Polling (Production Mode)
If you want the system to run autonomously without the map interface, start the master job scheduler. This will wake up every 15 minutes, check the static `mumbai_roi.geojson` area for new satellite passes, and process them automatically.

    python main.py