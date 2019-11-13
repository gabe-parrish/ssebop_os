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
from datetime import datetime, timedelta
from dateutil import relativedelta
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from SEEBop_os.raster_utils import raster_extract, x_y_extract

shape_root = r'Z:\Users\Gabe\UpperRioGrandeBasin\Shapefiles'
shape_name = r'station_metdata_wgs84.shp'
start = (2011, 1, 1)
end = (2017, 10, 31)
output_root = r'Z:\Users\Gabe\refET\met_datasets\gridmet_blankenau'

dt_start = datetime(start[0], start[1], start[2])
dt_end = datetime(end[0], end[1], end[2])
# time delta object of the period in between start and end
interval_td = dt_end - dt_start


shape_path = os.path.join(shape_root, shape_name)
# shape_path = r'Z:/Users/Gabe/UpperRioGrandeBasin/Shapefiles/testpoint_extract.shp'

x_y_dict = x_y_extract(point_path=shape_path, field='Location')
# x_y_dict = x_y_extract(point_path=shape_path, field='id')

print('xy dict \n', x_y_dict)


# TODO - Make a timeseries of Gridmet ETo paths.
# need a timeseries of datetimes

gridmet_ETo_root = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo'

print('days', interval_td.days)
gridmet_fileseries = []
dt_series = []
for i in range(interval_td.days + 1):
    dt = dt_start + relativedelta.relativedelta(days=i)
    year_dir = '{}'.format(dt.year)
    if dt.year <= 2010:
        filename = 'eto{}{:02d}{:02d}.tif'.format(dt.year, dt.month, dt.day)
        print('filename: {}'.format(filename))
    else:
        print(dt.strftime('%j'))
        filename = 'eto{}{}.tif'.format(dt.year, dt.strftime('%j'))

    eto_path = os.path.join(gridmet_ETo_root, year_dir, filename)
    gridmet_fileseries.append(eto_path)
    dt_series.append(dt)


for k, v in x_y_dict.items():
    x, y = v
    name = k
    if type(name) == str:
        name = name.strip(' ')
    print('name', name)
    vals = []
    dates = []
    for gmet_file, dtime in zip(gridmet_fileseries, dt_series):

        pixel_value = raster_extract(gmet_file, x=x, y=y)
        vals.append(pixel_value)
        dates.append(dtime)
    output_location = os.path.join(output_root, '{}.csv'.format(name))

    with open(output_location, 'w') as wfile:

        for v, d in zip(vals, dates):
            wfile.write('{},{}\n'.format(v,d))


