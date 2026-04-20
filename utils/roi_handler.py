import json
import os
from shapely.geometry import shape

def load_roi_as_wkt(geojson_path):
    """
    Loads a GeoJSON file and converts its first feature into a WKT string.
    WKT (Well-Known Text) is required by the CDSE OData API.
    """
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"❌ ROI file not found at: {geojson_path}")
        
    print(f"🗺️ Loading ROI from {geojson_path}...")
    
    with open(geojson_path, 'r') as file:
        geo_data = json.load(file)
        
    # GeoJSONs usually come as a FeatureCollection. We extract the first feature.
    try:
        geometry = geo_data["features"][0]["geometry"]
    except KeyError:
        raise ValueError("❌ Invalid GeoJSON structure. Ensure it is a FeatureCollection.")

    # Convert the raw JSON dictionary into a Shapely spatial object
    polygon_shape = shape(geometry)
    
    # Generate and return the WKT string
    wkt_string = polygon_shape.wkt
    
    return wkt_string

# --- TEST EXECUTION ---
if __name__ == "__main__":
    print("--- ROI HANDLER TEST ---")
    
    # Go up one level from utils to the project root, then into data folder
    test_path = os.path.join(os.path.dirname(__file__), "..", "data", "mumbai_roi.geojson")
    
    try:
        wkt_result = load_roi_as_wkt(test_path)
        print("✅ Conversion Successful!")
        print("WKT Output format required by API:")
        print(wkt_result)
    except Exception as e:
        print(e)