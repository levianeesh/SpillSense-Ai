import geopandas as gpd
import rasterio.features
import numpy as np

def create_water_mask(image_shape, spatial_profile):
    """Creates a binary mask (1 for water, 0 for land) matching the SAR image dimensions."""
    print("[LAND MASK] 🌍 Generating land mask using geographic coordinates...")
    
    # Fetch geographic boundaries remotely to avoid GeoPandas deprecation errors
    world_map_url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    
    try:
        world = gpd.read_file(world_map_url)
    except Exception as e:
        raise Exception(f"Failed to fetch geographic boundaries: {e}")
    
    # Extract projection mapping with a hard fallback to GPS coordinates (EPSG:4326)
    img_crs = spatial_profile.get('crs', 'EPSG:4326')
    img_transform = spatial_profile.get('transform')
    
    # Align coordinate systems
    world = world.to_crs(img_crs)
    
    # Rasterize (Burn the polygons into a NumPy array)
    land_mask = rasterio.features.rasterize(
        shapes=world.geometry,
        out_shape=image_shape,
        transform=img_transform,
        fill=1,          # Ocean becomes 1
        default_value=0, # Land shapes become 0
        dtype='uint8'
    )
    return land_mask

def apply_land_mask(image_array, spatial_profile):
    """Multiplies the SAR array by the water mask to completely black out landmasses."""
    mask = create_water_mask(image_array.shape, spatial_profile)
    
    print("[LAND MASK] ⬛ Masking out land pixels (Setting land to absolute 0)...")
    masked_array = image_array * mask
    
    return masked_array