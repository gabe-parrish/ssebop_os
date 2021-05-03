import os
# ============= standard library imports ========================
from SEEBop_os.raster_utils import gridmet_extract_point

"""Delaware Econet script to extract GRIDMET for use in Comparison"""

shape_root = r'C:\WaterSmart\Users\Gabe\refET\Delaware'
shape_name = r'Del_shape.shp'

gridmet_ETo_root = r'\\IGSKMNCNFS016\watersmartfs1\Data\ReferenceET\USA\Gridmet\Daily\ETo'

start = (1984, 1, 1)
end = (2017, 12, 31)

output = r'C:\WaterSmart\Users\Gabe\refET\Delaware\Del_GM_extract'
gridmet_extract_point(root=gridmet_ETo_root, shape_root=shape_root, shape_name=shape_name, start=start, end=end,
                      output_root=output, field='Call Sign', elevation_field='Elev (ft)', elevation_meters=False)

