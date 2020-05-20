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
from SEEBop_os.raster_utils import *

ppath = r'Z:\Users\Gabe\VegET\PotomacSample.shp'
sitename = 'DelOcean'

startyear = 2013
endyear = 2016
startday = 1
endday = 365

feat_dict = x_y_extract(point_path=ppath, field='id')
# print(feat_dict)

# I didn't realize that a key to a dictionary could be an interger
x, y = feat_dict[0]

# print(feat_dict.items())
#
# for i in feat_dict.items():
#     print('i', i)

root = r'Z:\Projects\Cloud_Veg_ET'

#'dd': {'folder': r'model_outputs\v1_DRB\dd', 'fmt': None, 'dt_fmt': 'doy'},
#     'etasw': {'folder': r'model_outputs\v1_DRB\etasw', 'fmt': None, 'dt_fmt': 'doy'},
#     'etasw5': {'folder': r'model_outputs\v1_DRB\etasw5', 'fmt': None, 'dt_fmt': 'doy'},
#     'rain': {'folder': r'model_outputs\v1_DRB\rain', 'fmt': None, 'dt_fmt': 'doy'},
#     'snowmelt': {'folder': r'model_outputs\v1_DRB\snowmelt', 'fmt': None, 'dt_fmt': 'doy'},
#     'snwpk': {'folder': r'model_outputs\v1_DRB\snwpck', 'fmt': None, 'dt_fmt': 'doy'},
#     'srf': {'folder': r'model_outputs\v1_DRB\srf', 'fmt': None, 'dt_fmt': 'doy'},
#     'swe': {'folder': r'model_outputs\v1_DRB\swe', 'fmt': None, 'dt_fmt': 'doy'},
#     'swf': {'folder': r'model_outputs\v1_DRB\swf', 'fmt': None, 'dt_fmt': 'doy'},
#     'swi': {'folder': r'model_outputs\v1_DRB\swi', 'fmt': None, 'dt_fmt': 'doy'},

# 'folder' gives the subdirectory location.
# 'fmt' goves the format of the .tif file to be extracted
# 'dt_fmt' gives a format YYYYdoy for daily time series, doy for climatology day-of-year
folder_dict = {
    'ndvi': {'folder': r'Data\NA_data_for_cloud\NDVI', 'fmt': '{}.250_m_16_days_NDVI.tif', 'dt_fmt': 'YYYYdoy'},
    'precip': {'folder': r'Data\NA_data_for_cloud\Precipitation_withHawaiiPuertoRico',
               'fmt': 'prec_{}.tif', 'dt_fmt': 'YYYYdoy'},
    'tavg': {'folder': r'Data\NA_data_for_cloud\Temperature\tavg_C_daily', 'fmt': 'tavg_{}.tif', 'dt_fmt': 'doy'},
    'tmax': {'folder': r'Data\NA_data_for_cloud\Temperature\tmax_C_daily', 'fmt': 'tmax_{}.tif', 'dt_fmt': 'doy'},
    'tmin': {'folder': r'Data\NA_data_for_cloud\Temperature\tmin_C_daily', 'fmt': 'tmin_{}.tif', 'dt_fmt': 'doy'}
}
# put the key and comma delimited stuff in the extraction dict. ts for timeseries, clim for climatological.
ts_extraction_dict = {}
clim_extraction_dict = {}
for k, v in folder_dict.items():

    ts_extraction_lst = []
    clim_extraction_lst = []

    fl = v['fmt'].split('{}')
    f = fl[0]
    l = fl[1]

    fpath = os.path.join(root, v['folder'])

    for path, dirs, files in os.walk(fpath):
        for f in files:

            if f.endswith('.tif'):
                print(f)

                if v['dt_fmt'] == 'doy':
                    print('the dataset is climatological')

                    # split from the ending 'l' and doy is the last three of the first of the list
                    doy = f.split(l)[0][-3:]
                    print('doy'), doy

                    # get the values of the point
                    raspath = os.path.join(path, f)
                    val = raster_extract(raster_path=raspath, x=x, y=y, arc=False)
                    line = '{},{}'.format(doy, val)
                    clim_extraction_lst.append(line)

                elif v['dt_fmt'] == 'YYYYdoy':
                    print('the dataset is daily time-series')
                    ydoy = f.split(l)[0]#[-7:]
                    print('ydoy', ydoy)

                    # get the values of the point
                    raspath = os.path.join(path, f)
                    val = raster_extract(raster_path=raspath, x=x, y=y, arc=False)
                    line = '{},{}'.format(ydoy, val)
                    ts_extraction_lst.append(line)

    # for ndvi, or whatever variable, set the values into the dictionary
    ts_extraction_dict[k] = ts_extraction_lst
    clim_extraction_dict[k] = clim_extraction_lst


with open(os.path.join(root, 'climatologies_ext_{}.txt'.format(sitename)), 'w') as wfile:
    for i, (k, v) in enumerate(clim_extraction_dict.items()):

        if i == 0:
            # write the header
            wfile.write('-------------\n')
            wfile.write('var,day,val\n')
            wfile.write('-------------\n')
            wfile.write('{},{}\n'.format(k, v[i]))
        else:
            wfile.write('{},{}\n'.format(k, v[i]))



with open(os.path.join(root, 'climatologies_ext_{}.txt'.format(sitename)), 'w') as wfile:
    for i, (k, v) in enumerate(ts_extraction_dict.items()):
        if i == 0:
            # write the header
            wfile.write('-------------\n')
            wfile.write('var,day,val\n')
            wfile.write('-------------\n')
            wfile.write('{},{}\n'.format(k, v[i]))
        else:
            wfile.write('{},{}\n'.format(k, v[i]))





# # probably should be arc = True, but it doesn't really matter here since any pixel will do.
# raster_extract(raster_path=None, x=x, y=y, arc=False)
