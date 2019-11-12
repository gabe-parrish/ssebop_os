# ===============================================================================
# Copyright 2019 Gabriel Parrish
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from SEEBop_os.raster_utils import raster_extract, x_y_extract

shape_root = r'Z:\Users\Gabe\UpperRioGrandeBasin\Shapefiles'
shape_name = r'station_metdata.shp'
start = (2011, 1, 1)
end = (2019, 10, 31)



shape_path = os.path.join(shape_root, shape_name)

x_y_dict = x_y_extract(point_path=shape_path, field='Location')

print('xy dict \n', x_y_dict)


# TODO - Make a timeseries of Gridmet ETo paths.
# need a timeseries of datetimes

gridmet_ETo_root = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo'