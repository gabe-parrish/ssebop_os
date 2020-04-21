# ===============================================================================
# Created: March 2020
# Authors: Gabriel Parrish, Stefanie Kagone
# Description: Use GDAL warp comment to modify input data for Cloud Veg ET model

# ===============================================================================

import os
import gdal
from gdalconst import *
from subprocess import call


"""
Delaware Original Boundary
    # conus WGS 84 Geographic ORIGINAL NDVI extent resolution
    49667, 14416
    # resolution
    0.0020810045, 0.0020810045
    # top
    50.000001907
    # left
    -155.572381973
    # right
    -52.2151328166
    #bottom
    20.0002414254
    
Delaware Area of Interest
Y maximum: 45.0
Y Minimum: 37.0
X Minimum: -76.0
X Maximum: -70.0
Nodata: -3.402823e+38
Maintain Clipping Extent False

cols: 11573
rows: 28061

"""

def warp(initial_projection, final_projection, resampling_method, dimx, dimy, xmin, ymin, xmax,
         ymax, input_path, output_path):
    """

    :param initial_projection:
    :param final_projection:
    :param resampling_method:
    :param dimx:
    :param dimy:
    :param xmin:
    :param ymin:
    :param xmax:
    :param ymax:
    :param input_path:
    :param output_path:
    :return:
    """
    print(resampling_method)
    warpcommand = "gdalwarp -overwrite -s_srs {} -t_srs {} -r {} -ts {} {} -te {} {} {} {} -of GTiff {} " \
                  "{}".format(initial_projection, final_projection, resampling_method, dimx, dimy, xmin, ymin, xmax,
                              ymax, input_path, output_path)
    print('warp command', warpcommand)

    #Metadata file
    #with open(os.path.join('{}meta.txt'.format(output_path)), 'w') as wfile:
    #    wfile.write(warpcommand)

    # Actually starts the warp.
    call(warpcommand, shell=True)

def run():
    """
    Based on user-specified dimensions, extent, projection and resampling method, this script will warp and resample all
    geotiff files in a given directory.
    """

    os.environ['GDAL_DATA'] = r'C:\Users\skagone\AppData\Local\Continuum\miniconda3\envs\gdal_env\Library\share\gdal'
    os.environ['PROJ_LIB'] = r'C:\Users\skagone\AppData\Local\Continuum\miniconda3\envs\gdal_env\Library\share\proj'

    root_path = r'W:\Projects\Veg_ET\USA_data\temperature_gridmet\tmax_gridmet\Med_tmax_1984_2017_C'
    var_name = 'TMAX'
    output_root = os.path.join(r'C:\WaterSmart\Projects\CloudVegET\DATA\TEMP', var_name)
    if not os.path.exists(output_root):
        os.makedirs(output_root)

    initial_projection = 'EPSG:4326'
    final_projection = 'EPSG:4326'
    resampling_method = 'near'
    dimx = 1938
    dimy = 3124
    xmin = -77.022786801
    ymin = 37.0082889025
    xmax = -72.98980008
    ymax = 43.5093469605

    # we 'walk' through each file in the directory and warp it to our user defined specifications...
    walk_obj = os.walk(root_path)
    for path, subdir, files in walk_obj:
        for file in files:
            if file.endswith('.tif'):
                header = file.split('.')[0]   # + '.' + file.split('.')[1]
                newfilename = "{}{}".format(header, "_gw.tif")
                input_path = os.path.join(path, file)
                output_path = os.path.join(output_root, newfilename)
                warp(initial_projection, final_projection, resampling_method, dimx, dimy, xmin,
                     ymin, xmax, ymax, input_path, output_path)


    # input_path = os.path.join(root_path, r'2015002.250_m_NDVI.tif')
    # output_path = os.path.join(output_root, r'RGV_NDVITest_warp.tif')
    # warp(initial_projection, final_projection, resampling_method, dimx, dimy, xmin, ymin, xmax, ymax, input_path, output_path)


if __name__ == "__main__":
    run()

