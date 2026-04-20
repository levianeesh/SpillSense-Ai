import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load hidden credentials
load_dotenv()
CDSE_USERNAME = os.getenv("CDSE_USERNAME")
CDSE_PASSWORD = os.getenv("CDSE_PASSWORD")

AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

def get_access_token():
    """Trades username and password for a secure access token."""
    if not CDSE_USERNAME or not CDSE_PASSWORD:
        raise ValueError("Credentials missing! Please check your .env file.")

    print("🔑 Authenticating with CDSE...")
    payload = {
        "client_id": "cdse-public",
        "username": CDSE_USERNAME,
        "password": CDSE_PASSWORD,
        "grant_type": "password"
    }
    
    response = requests.post(AUTH_URL, data=payload)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"❌ Auth failed: {response.status_code} - {response.text}")

def build_search_query(wkt_polygon, hours_back=6):
    """
    Builds the OData URL including Time, Product Type (GRDH), and Spatial ROI.
    Note: We use 6 hours back here for testing to ensure we find at least one image.
    """
    now = datetime.utcnow()
    past_time = now - timedelta(hours=hours_back)
    time_str = past_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    # The exact format CDSE requires for spatial queries (SRID=4326 means standard GPS coordinates)
    spatial_filter = f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt_polygon}')"
    
    filter_query = (
        f"Collection/Name eq 'SENTINEL-1' and "
        f"contains(Name,'_GRDH_') and "
        f"ContentDate/Start gt {time_str} and "
        f"{spatial_filter}"
    )
    
    # Order by date descending to get the absolute newest image first
    query_url = f"{ODATA_URL}?$filter={filter_query}&$top=5&$orderby=ContentDate/Start desc"
    return query_url

def execute_search(access_token, query_url):
    """
    Sends the request to CDSE and extracts the list of available images.
    """
    print("📡 Sending search query to CDSE Catalogue...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(query_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"❌ API Query Failed: {response.status_code} - {response.text}")
        
    data = response.json()
    
    # CDSE stores the results in a key called 'value'
    results = data.get("value", [])
    
    parsed_images = []
    for item in results:
        parsed_images.append({
            "id": item["Id"],            # The unique UUID we need for downloading
            "name": item["Name"],        # The SAFE filename
            "size_mb": item["ContentLength"] / (1024 * 1024) if item.get("ContentLength") else 0
        })
        
    return parsed_images

# --- TEST EXECUTION ---
if __name__ == "__main__":
    # To test this, we will import our ROI handler from the previous stage
    from roi_handler import load_roi_as_wkt
    
    print("--- CDSE SEARCH EXECUTION TEST ---")
    try:
        # 1. Load the polygon
        roi_path = os.path.join(os.path.dirname(__file__), "..", "data", "mumbai_roi.geojson")
        wkt_polygon = load_roi_as_wkt(roi_path)
        
        # 2. Authenticate
        token = get_access_token()
        print("✅ Access token acquired.")
        
        # 3. Build the query
        url = build_search_query(wkt_polygon, hours_back=48) # Searching back 48 hrs just to guarantee a hit in tests
        
        # 4. Execute the search
        found_images = execute_search(token, url)
        
        print(f"\n✅ Search complete! Found {len(found_images)} images matching criteria.")
        for img in found_images:
            print(f"- ID: {img['id']} | Name: {img['name']} | Size: {img['size_mb']:.2f} MB")
            
    except Exception as e:
        print(e)