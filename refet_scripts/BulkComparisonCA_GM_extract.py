import os
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from SEEBop_os.raster_utils import gridmet_extract_point

"""CA CIMIS met script to extract GRIDMET for use in Comparison"""

# TODO - error w one of the sites F.S.U USDA

shape_root = r'\\IGSKMNCNFS016\watersmartfs1\Users\Gabe\refET\CIMIS'
shape_name = r'CIMIS_shape_namefix.shp'

gridmet_ETo_root = r'\\IGSKMNCNFS016\watersmartfs1\Data\ReferenceET\USA\Gridmet\Daily\ETo'

start = (1984, 1, 1)
end = (2017, 12, 31)

output = r'\\IGSKMNCNFS016\watersmartfs1\Users\Gabe\refET\CIMIS\CA_GRIDMET'
gridmet_extract_point(root=gridmet_ETo_root, shape_root=shape_root, shape_name=shape_name, start=start, end=end,
                      output_root=output, field='Name', elevation_field='ELEV', elevation_meters=True)