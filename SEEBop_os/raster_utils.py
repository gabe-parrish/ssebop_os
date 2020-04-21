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
import gdal
import ogr
import sys
from dateutil import relativedelta
from datetime import date, datetime
import pandas as pd

# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat

# for the local machine
os.environ['GDAL_DATA'] = r'C:\Users\gparrish\AppData\Local\conda\conda\envs\gdal_env\Library\share\gdal'

"""This script stores functions related to reading and writing raster data using GDAL"""
def val_extract(point_path, field='id', other_field='Elevation'):

    """For extracting other characteristics from a shapefile and saving to a dict. To be used in conjunction with x_y extract"""

    # get an appropriate driver
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # open the shapefile. Use 0 for read-only mode.
    datasource_obj = driver.Open(point_path, 0)
    if datasource_obj is None:
        print("cannot open {}".format(point_path))
        sys.exit(1)

    # get the layer object from the datasource
    layer_obj = datasource_obj.GetLayer()

    # get the features in the layer
    feature_count = layer_obj.GetFeatureCount()

    print("there are {} features".format(feature_count))

    # # get the feature of the shapefile. You can loop through features, but there should only be one.
    # feature = layer_obj.GetFeature(2)

    feature_dict = {}
    for i in range(1, feature_count + 1, 1):
        feature = layer_obj.GetNextFeature()

        # you could get a features 'fields' like feature.GetField('id')
        field_value = feature.GetField(field)

        print("field -> {}".format(field_value))
        other_value = feature.GetField(other_field)

        feature_dict[field_value] = other_value

        # housekeeping
        feature.Destroy()  # always destroy the feature before the datasource

    # housekeeping
    datasource_obj.Destroy()

    return feature_dict

def x_y_extract(point_path, field='id'):
    """
    This extracts the x and y raster grid coordinates from a point shapefile
    :param point_path: string path to point shapefile
    :return:
    """
    # get an appropriate driver
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # open the shapefile. Use 0 for read-only mode.
    datasource_obj = driver.Open(point_path, 0)
    if datasource_obj is None:
        print("cannot open {}".format(point_path))
        sys.exit(1)

    # get the layer object from the datasource
    layer_obj = datasource_obj.GetLayer()

    # get the features in the layer
    feature_count = layer_obj.GetFeatureCount()

    print("there are {} features".format(feature_count))

    # # get the feature of the shapefile. You can loop through features, but there should only be one.
    # feature = layer_obj.GetFeature(2)

    feature_dict = {}
    for i in range(1, feature_count+1, 1):

        feature = layer_obj.GetNextFeature()

        # you could get a features 'fields' like feature.GetField('id')
        field_value = feature.GetField(field)

        print("field -> {}".format(field_value))

        # but we just want the geometry of the feature
        geometry = feature.GetGeometryRef()

        # get the x and y
        x = geometry.GetX()
        y = geometry.GetY()

        print("x -> {}, y -> {}".format(x, y))

        feature_dict[field_value] = (x, y)

        # housekeeping
        feature.Destroy()  # always destroy the feature before the datasource

    # housekeeping
    datasource_obj.Destroy()

    return feature_dict


def raster_extract(raster_path, x, y, arc=True):
    """
    uses x and y from x_y_extract function to grab the value at the cordinates from the raster given in raster_path
    :param raster_path:
    :param x:
    :param y:
    :return:
    """

    # don't forget to register
    gdal.AllRegister()

    # open the raster datasource
    datasource_obj = gdal.Open(raster_path)
    if datasource_obj is None:
        print("Can't open the datasource from {}".format(raster_path))
        sys.exit(1)

    # get the size of image (for reading)
    rows = datasource_obj.RasterYSize
    cols = datasource_obj.RasterXSize

    print('rows and cols \n', rows, cols)

    # get georefference info to eventually calculate the offset:
    transform = datasource_obj.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    print('xy origin', xOrigin, yOrigin)
    width_of_pixel = transform[1]
    height_of_pixel = transform[5]

    print('widht and height \n', width_of_pixel, height_of_pixel)

    # read in a band (only one band)
    band = datasource_obj.GetRasterBand(1)
    # ReadAsArray(xoffset, yoffset, xcount, ycount)
    data = band.ReadAsArray(0, 0, cols, rows)

    print('shape:', data.shape)

    # get the offsets so you can read the data from the correct position in the array.
    print(x, xOrigin, width_of_pixel)
    print(y, yOrigin, height_of_pixel)
    x_offset = int((x - xOrigin) / width_of_pixel)
    y_offset = int((y - yOrigin) / height_of_pixel)

    print('offset\n',x_offset, y_offset)

    # is this a [rows, columns] thing?
    try:
        value = data[y_offset, x_offset]
    except IndexError:
        print('INDEX ERROR, ASSUMING that we are using mini-models and that the array is 3X3 and taking center value')
        value = data[1, 1]
    # print "VALUE {}".format(value)

    # # housekeeping
    # datasource_obj.Destroy()

    return value


def gridmet_extract_point(root, shape_root, shape_name, start, end, output_root, field='id',
                          elevation_field='Elevation', elevation_meters=True):
    """
    writes a csv for each field present in a point shapefile
    :param shape_root:
    :param shape_name:
    :param start:
    :param end:
    :param output_root:
    :return:
    """
    dt_start = datetime(start[0], start[1], start[2])
    dt_end = datetime(end[0], end[1], end[2])
    # time delta object of the period in between start and end
    interval_td = dt_end - dt_start

    shape_path = os.path.join(shape_root, shape_name)
    # shape_path = r'Z:/Users/Gabe/UpperRioGrandeBasin/Shapefiles/testpoint_extract.shp'

    x_y_dict = x_y_extract(point_path=shape_path, field=field)
    # x_y_dict = x_y_extract(point_path=shape_path, field='id')
    elev_dict = val_extract(point_path=shape_path, field=field, other_field=elevation_field)

    print('xy dict \n', x_y_dict)
    print('days', interval_td.days)

    gridmet_fileseries = []
    dt_series = []
    for i in range(interval_td.days + 1):
        dt = dt_start + relativedelta.relativedelta(days=i)
        year_dir = '{}'.format(dt.year)
        # if dt.year >= 2012:
        #     filename = 'eto{}{:02d}{:02d}.tif'.format(dt.year, dt.month, dt.day)
        #     print('filename: {}'.format(filename))
        # else:
        print(dt.strftime('%j'))
        filename = 'eto{}{}.tif'.format(dt.year, dt.strftime('%j'))

        eto_path = os.path.join(root, year_dir, filename)
        gridmet_fileseries.append(eto_path)
        dt_series.append(dt)

    for k, v in x_y_dict.items():
        elev = elev_dict[k]
        if type(elev) == int or type(elev) == float:
            pass
        else:
            elev = ''.join(c for c in elev if c.isdigit())
        elev = int(elev)
        if not elevation_meters:
            # convert feet to meters
            elev *= 0.3048
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
                wfile.write('{},{},{},{},{}\n'.format(v, d, x, y, elev))


def convert_raster_to_array(input_raster_path, raster=None, band=1):
    """
    Convert .tif raster into a numpy numerical array.

    :rtype: object
    :param input_raster_path: Path to raster.
    :param raster: Raster name with \*.tif
    :param band: Band of raster sought.

    :return: Numpy array.
    """
    # print "input raster path", input_raster_path
    # print "raster", raster
    p = input_raster_path
    if raster is not None:
        p = os.path.join(p, raster)

    # print "filepath", os.path.isfile(p)
    # print p
    if not os.path.isfile(p):
        print
        'Not a valid file: {}'.format(p)

    raster_open = gdal.Open(p)
    ras = raster_open.GetRasterBand(band).ReadAsArray()
    return ras



def gridmet_eto_reader(gridmet_eto_loc, smoothing=False):
    """
    This function is for reading gridmet files generated by this script
    :param gridmet_eto_loc: string path to gridmet file
    :return: dataframe
    """

    gridmet_dict = {'ETo':[], 'date':[], 'Lon':[], 'Lat':[], 'elevation_m':[]}

    with open(gridmet_eto_loc, 'r') as rfile:
        for line in rfile:
            line = line.strip('\n')
            vars = line.split(',')
            gridmet_dict['ETo'].append(float(vars[0]))
            gridmet_dict['date'].append(vars[1])
            gridmet_dict['Lon'].append(float(vars[2]))
            gridmet_dict['Lat'].append(float(vars[3]))
            gridmet_dict['elevation_m'].append(float(vars[4]))


    gm_df = pd.DataFrame(gridmet_dict, columns=['ETo', 'date', 'Lon', 'Lat', 'elevation_m'])

    gm_df['dt'] = pd.to_datetime(gm_df['date'])

    gm_df.set_index('dt', inplace=True)

    if smoothing:
        print('smoothing is set to True, so calculating 10day running average of ETo timeseries for gridmet')
        gm_df = gm_df.rolling('10D').mean()
        # gm_df = gm_df.resample('1M').sum()
    # test
    print(gm_df)
    return gm_df



# def gridmet_extract_points(root, shape_root, shape_name, start, end, output_root, field='id'):
#     """
#         writes multiple csvs corresponding to multiple shapes in a shapefile.
#         :param shape_root:
#         :param shape_name:
#         :param start:
#         :param end:
#         :param output_root:
#         :return:
#         """
#     dt_start = datetime(start[0], start[1], start[2])
#     dt_end = datetime(end[0], end[1], end[2])
#     # time delta object of the period in between start and end
#     interval_td = dt_end - dt_start
#
#     shape_path = os.path.join(shape_root, shape_name)
#     # shape_path = r'Z:/Users/Gabe/UpperRioGrandeBasin/Shapefiles/testpoint_extract.shp'
#
#     x_y_dict = x_y_extract(point_path=shape_path, field=field)
#     # x_y_dict = x_y_extract(point_path=shape_path, field='id')
#
#     print('xy dict \n', x_y_dict)
#     print('days', interval_td.days)
#
#     gridmet_fileseries = []
#     dt_series = []
#     for i in range(interval_td.days + 1):
#         dt = dt_start + relativedelta.relativedelta(days=i)
#         year_dir = '{}'.format(dt.year)
#         if dt.year <= 2010:
#             filename = 'eto{}{:02d}{:02d}.tif'.format(dt.year, dt.month, dt.day)
#             print('filename: {}'.format(filename))
#         else:
#             print(dt.strftime('%j'))
#             filename = 'eto{}{}.tif'.format(dt.year, dt.strftime('%j'))
#
#         eto_path = os.path.join(root, year_dir, filename)
#         gridmet_fileseries.append(eto_path)
#         dt_series.append(dt)
#
#     for k, v in x_y_dict.items():
#         x, y = v
#         name = k
#         if type(name) == str:
#             name = name.strip(' ')
#         print('name', name)
#         vals = []
#         dates = []
#         for gmet_file, dtime in zip(gridmet_fileseries, dt_series):
#             pixel_value = raster_extract(gmet_file, x=x, y=y)
#             vals.append(pixel_value)
#             dates.append(dtime)
#         output_location = os.path.join(output_root, '{}.csv'.format(name))
#
#         with open(output_location, 'w') as wfile:
#
#             for v, d in zip(vals, dates):
#                 wfile.write('{},{}\n'.format(v, d))

# def run_point_extract(point_path, raster_path, ending, landsat=False, sseb=False, output_path=None):
#     """
#
#     :param output_path:
#     :param point_path:
#     :param raster_path:
#     :param ending:
#     :return:
#     """
#
#     # Begin extraction from the point path.
#     feature_dictionary = x_y_extract(point_path)
#     print("feature dictionary", feature_dictionary)
#
#     # Use the feature dictionary to extract data from the rasters.
#     for feature, tup in feature_dictionary.iteritems():
#
#         # Get the X and Y coords from the dictionary and unpack them
#         x, y = tup
#         print(x, y)
#
#         # === Iterate the rasters ===
#
#         # Containers to hold the dates and values for the rasters
#         raster_date = []
#         raster_values = []
#
#         sseb_dict = {}
#
#         # store the raster values and image dates for the x and y coordinate pair into the lists
#         for path, dir, file in os.walk(raster_path, topdown=False):
#
#             print(path, dir, file)
#
#             for file in file:
#                 if file.endswith(ending):
#
#                     # path to the raster file
#                     raster_address = os.path.join(path, file)
#
#
#                     if landsat:
#
#                         # Format the date into dt object
#                         date_str = file.split('_')[0]
#                         date_str = date_str[-12:-5]
#
#                         print("date string {}".format(date_str))
#                         # get a datetime object from a julian date
#                         r_date = datetime.strptime(date_str, '%Y%j').date()
#                         raster_date.append(r_date)
#
#                     if sseb:
#                         name = file.split('.')[0]
#                         year = int(name.split('_')[-2])
#                         month = int(name.split('_')[-1])
#                         r_date = date(year, month, 1)
#                         raster_date.append(r_date)
#
#
#                     # get the raster value using raster_extract() function
#                     value = raster_extract(raster_address, x, y)
#                     raster_values.append(value)
#
#         if landsat:
#             # format the values from the different dates into a dataframe
#             output_dict = {'date': raster_date, 'value': raster_values}
#             output_df = pd.DataFrame(output_dict, columns=['date', 'value'])
#             csv_path = os.path.join(output_path, "point_shape_id_{}.csv".format(feature))
#
#             # use the pandas.to_csv() method to output to csv
#             output_df.to_csv(csv_path)
#
#         if sseb:
#             output_dict = {'date': raster_date, 'value': raster_values}
#
#             sseb_dict['{}'.format(feature)] = output_dict
#
#     if sseb:
#         return sseb_dict
#
#
#     print("COMPLETE")

