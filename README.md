# Near Real-Time Oil Spill Detection System 

Welcome to the documentation for the Near Real-Time (NRT) Oil Spill Detection System backend. This project is designed to automatically ingest and prepare satellite radar imagery to monitor coastal environments. 

**⚠️ PROJECT STATUS: INCOMPLETE (STAGES 1-9 ONLY)**
*This system is currently under active development. The current pipeline handles automated scheduling, API querying, safe chunked downloading, and memory-efficient array loading. Future stages (Machine Learning Inference, Land Masking, and Alerting) are strictly excluded from this current release and will be implemented in later phases.*

---

## 🚀 Getting Started (Runnable Instructions)

To run this backend system locally or in a cloud environment like Google Colab, follow these steps strictly:

1. **Clone the Repository:** Pull this codebase to your local machine or cloud environment and navigate into the project directory.
   ```bash
   git clone [https://github.com/Spectrae/SpillSense-Ai.git](https://github.com/Spectrae/SpillSense-Ai.git)
   cd SpillSense-Ai
   ```
2. **Install Dependencies:** Run the following command to install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables:** Create a `.env` file in the root directory (do NOT commit this to version control) and add your Copernicus Data Space Ecosystem (CDSE) credentials:
   ```env
   CDSE_USERNAME=your_registered_email@example.com
   CDSE_PASSWORD=your_super_secret_password
   ```
4. **Execute the Polling System:** Start the master orchestrator. It will immediately run a startup check and then enter a 15-minute polling loop:
   ```bash
   python main.py
   ```

---

## STAGE 1: System Architecture Overview

System architecture is the blueprint of our software. Before writing complex ML or API code, we need to know exactly how data flows from point A to point B. Think of it like a factory assembly line.

**Current Pipeline Flow:**
```text
[CDSE API (Space Data)]
       | (Polls strictly every 15 mins via UTC)
       v
[1. Job Scheduler] -> (Triggers Pipeline)
       |
       v
[2. API Connector & ROI Handler] -> (Finds matching Sentinel-1 GRD files)
       |
       v
[3. Chunked Downloader] -> (Streams 1GB+ .zip to disk & extracts .SAFE)
       |
       v
[4. Preprocessor] -> (Locates VV TIFF & loads into memory as NumPy Array)
       |
       v
[ 🚧 SYSTEM STOPS HERE - ML & ALERTS PENDING 🚧 ]
```

---

## STAGE 2: Tech Stack Table

Choosing the right tools is just as critical as writing the code. Because our system must run on free cloud environments... we have to be lightweight.

| Technology | Purpose | Alternatives | Future Scope |
| :--- | :--- | :--- | :--- |
| **Python 3.10+** | Core backend logic, automation, and API orchestration. | C++, Go | Refactoring into specialized microservices. |
| **CDSE API (OData)** | Querying and downloading Sentinel-1 SAFE satellite files. | ASF DAAC | Adding Sentinel-2 (optical) data correlation. |
| **rasterio & shapely** | Opening complex SAR imagery arrays and defining ROI polygons. | GDAL (hard to install), ESA SNAP (too heavy for Colab) | Cloud Optimized GeoTIFF (COG) streaming. |
| **APScheduler** | Handling the reliable 15-minute polling loop inside Python. | Linux cron, `time.sleep` | Migrating to Apache Airflow for complex DAG logic. |
| **Google Colab** | The free cloud execution environment. | AWS EC2, Hugging Face Spaces | Containerizing the whole system with Docker. |

---

## STAGE 3: Understanding Sentinel-1 SAR Data

Before you process data, you must understand the physics of what you are looking at. 

* [cite_start]**What is SAR?** Synthetic Aperture Radar (SAR) shoots microwave pulses down to Earth and listens for the "echo" (backscatter)[cite: 350]. [cite_start]Because it uses its own energy (microwaves), it can "see" through clouds, rain, and complete darkness[cite: 351].
* [cite_start]**Why used for oil spill detection?** Rough surfaces scatter the radar pulse in all directions, so some of it returns to the satellite (making the ocean look grey)[cite: 353]. [cite_start]However, oil is thick and viscous[cite: 354]. [cite_start]It smooths out the ocean waves[cite: 354]. [cite_start]When the radar pulse hits this smooth, mirror-like oil surface, the pulse bounces away into space (specular reflection)[cite: 355]. [cite_start]Therefore, oil spills appear as completely dark black patches on a SAR image[cite: 356].

[cite_start]We also utilize a Metadata Parser (`s1_parser.py`) to strictly filter out data we don't want and only accept GRD (Ground Range Detected) data[cite: 360, 361].

---

## STAGE 4: CDSE API Deep Dive

[cite_start]We talk directly to their servers using an API[cite: 461]. CDSE uses a two-step system:
1.  [cite_start]**Authentication (Keycloak):** We send our username and password to an "Auth Server" to retrieve a secure "Access Token"[cite: 463, 464].
2.  [cite_start]**Querying (OData):** We send this Access Token to the "Catalogue Server" along with a search question[cite: 465]. 

[cite_start]We use `python-dotenv` to ensure we NEVER hardcode passwords in our Python files[cite: 467, 472].

---

## STAGE 5: ROI Polygon Setup

[cite_start]Sentinel-1 captures massive strips of the Earth—often 250 kilometers wide[cite: 575]. [cite_start]If you process the entire strip for oil spills, your server will crash due to lack of memory (RAM)[cite: 576]. 

[cite_start]We define a virtual fence (a polygon) around our target area[cite: 578]. [cite_start]To tell computers about this shape, we use GeoJSON[cite: 580]. [cite_start]However, the CDSE API requires coordinates in a format called WKT (Well-Known Text)[cite: 581]. [cite_start]Our `roi_handler.py` module uses `shapely` to instantly translate our local `.geojson` file into an API-readable WKT string[cite: 584, 587].

---

## STAGE 6: Polling System Design

[cite_start]We need our system to wake up every 15 minutes, check the CDSE API, and go back to sleep[cite: 693]. [cite_start]We use an App-Level scheduler (`APScheduler`) because in managed cloud environments, you rarely have reliable root access to configure Linux OS-level cron jobs[cite: 698, 700]. 

[cite_start]We configure `BlockingScheduler` to strictly use UTC time (crucial for satellite data) and set `max_instances=1` to ensure that if a massive satellite download takes longer than 15 minutes, it won't accidentally start a second overlapping download[cite: 703, 705, 711].

---

## STAGE 7: Python Script to Query CDSE API

[cite_start]We combine our Access Token and our WKT Polygon to send an HTTP GET request[cite: 796, 797]. [cite_start]We construct an OData URL filtering for `SENTINEL-1`, `_GRDH_` (Ground Range Detected High-Resolution) imagery, and apply the exact spatial filter required by CDSE: `OData.CSC.Intersects`[cite: 480, 803].

[cite_start]If successful, the server responds with a JSON file containing a list of satellite images that match our criteria, allowing us to extract their unique download IDs[cite: 798, 800].

---

## STAGE 8: Auto Download Sentinel-1 Data

[cite_start]Sentinel-1 GRD files are massive—usually around 1 Gigabyte each[cite: 938]. [cite_start]If we tell Python to just "download it," Python will try to load the entire 1GB file into your server's RAM all at once[cite: 938]. [cite_start]In Google Colab or Hugging Face Spaces, this will cause an "Out of Memory" (OOM) crash instantly[cite: 939].

[cite_start]We use **Chunked Streaming** using `requests (with stream=True)`[cite: 940, 948]. [cite_start]We tell the server to send the file in tiny 8MB chunks, writing each chunk directly to the hard drive, bypassing the RAM entirely[cite: 940, 941]. [cite_start]We then use Python's built-in `zipfile` library to automatically extract the `.SAFE` directory[cite: 942, 949].

---

## STAGE 9: Preprocessing Pipeline (Data Extraction Only)

*Note: For this project iteration, we are strictly limiting preprocessing to array extraction.*

[cite_start]We use Custom Python (`rasterio` + `numpy`) over ESA SNAP because it is extremely lightweight and runs perfectly in Colab[cite: 1062].

[cite_start]The SAFE folder we downloaded in Stage 8 contains dozens of files[cite: 1067]. We execute two steps:
1.  [cite_start]**Find VV TIFF:** We dig into that folder to extract specifically the VV polarization `.tiff` file[cite: 1068]. [cite_start]Vertical transmit, Vertical receive (VV) is standard for ocean monitoring because sea waves reflect VV strongly, making the ocean look bright, while oil smooths the ocean, making it look dark[cite: 1069, 1070].
2.  [cite_start]**Load Array:** We safely open the massive `.tiff` file in memory as a matrix of numbers (a 2D NumPy array) using `rasterio`[cite: 1073, 1077].

*(Pipeline halts here. Normalization, speckle filtering, masking, and ML are intentionally omitted.)*

---

## 📁 Full Project Structure

Ensure your local directory strictly matches this structure to prevent import errors:

```text
/project_root
├── .env
├── main.py
├── requirements.txt
├── data/
│   └── mumbai_roi.geojson
└── utils/
    ├── s1_parser.py
    ├── cdse_api.py
    ├── roi_handler.py
    ├── downloader.py
    └── preprocessor.py
```