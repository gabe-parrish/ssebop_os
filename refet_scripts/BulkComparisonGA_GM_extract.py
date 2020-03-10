import os
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from SEEBop_os.raster_utils import gridmet_extract_point

"""GEORGIA state met script to extract GRIDMET for use in Comparison"""

shape_root = r'\\IGSKMNCNFS016\watersmartfs1\Users\Gabe\refET\Georgia_UGAWN'
shape_name = r'UGAWN_shape.shp'

gridmet_ETo_root = r'\\IGSKMNCNFS016\watersmartfs1\Data\ReferenceET\USA\Gridmet\Daily\ETo'

start = (1984, 1, 1)
end = (2017, 12, 31)

output = r'\\IGSKMNCNFS016\watersmartfs1\Users\Gabe\refET\Georgia_UGAWN\UGAWN_GRIDMET'
gridmet_extract_point(root=gridmet_ETo_root, shape_root=shape_root, shape_name=shape_name, start=start, end=end,
                      output_root=output, field='City', elevation_field='Elevation', elevation_meters=True)